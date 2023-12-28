#include <memory.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <fcntl.h>
#include <iostream>
#include <stdio.h>
#include "page.h"
#include "buf.h"

#define ASSERT(c)                                              \
    {                                                          \
        if (!(c))                                              \
        {                                                      \
            cerr << "At line " << __LINE__ << ":" << endl      \
                 << "  ";                                      \
            cerr << "This condition should hold: " #c << endl; \
            exit(1);                                           \
        }                                                      \
    }

//----------------------------------------
// Constructor of the class BufMgr
//----------------------------------------

BufMgr::BufMgr(const int bufs)
{
    numBufs = bufs;

    bufTable = new BufDesc[bufs];
    memset(bufTable, 0, bufs * sizeof(BufDesc));
    for (int i = 0; i < bufs; i++)
    {
        bufTable[i].frameNo = i;
        bufTable[i].valid = false;
    }

    bufPool = new Page[bufs];
    memset(bufPool, 0, bufs * sizeof(Page));

    int htsize = ((((int)(bufs * 1.2)) * 2) / 2) + 1;
    hashTable = new BufHashTbl(htsize); // allocate the buffer hash table

    clockHand = bufs - 1;
}

BufMgr::~BufMgr()
{

    // flush out all unwritten pages
    for (int i = 0; i < numBufs; i++)
    {
        BufDesc *tmpbuf = &bufTable[i];
        if (tmpbuf->valid == true && tmpbuf->dirty == true)
        {

#ifdef DEBUGBUF
            cout << "flushing page " << tmpbuf->pageNo
                 << " from frame " << i << endl;
#endif

            tmpbuf->file->writePage(tmpbuf->pageNo, &(bufPool[i]));
        }
    }

    delete[] bufTable;
    delete[] bufPool;
}

/**
 * @brief allocBuff checks if there is an available frame within the buffer pool
 *        for storing a new page and stores the available frame number in the passed on frame pointer
 *
 * @param frame address of frame variable to store the available frame index
 * @return const Status status code of the method returning OK when the method successfully finds an empty frame
 */
const Status BufMgr::allocBuf(int &frame)
{
    // Variable for storing the current status to be returned in the each stage of the method
    Status currStatus = OK;
    // increments every loop and exits once it loops around the clock two times
    int checkedFrameCnt = 0;
    bool found = false;
    while (checkedFrameCnt < numBufs * 2)
    {
        advanceClock();
        checkedFrameCnt++;

        BufDesc &currBufDesc = bufTable[clockHand];
        // if the state of the frame at the location clock hand is invalid then store the location in frame pointer
        if (!currBufDesc.valid)
        {
            found = true;
            break;
        }
        // if refbit is true change to false and move on to next frame
        if (currBufDesc.refbit)
        {
            currBufDesc.refbit = false;
            continue;
            // if refbit is false we check other conditions
        }
        else
        {
            // if pincouont is 0 no one is currently using this frame
            if (currBufDesc.pinCnt == 0)
            {
                // if current frame is dirty we flush dirty data to db
                if (currBufDesc.dirty)
                {
                    currStatus = currBufDesc.file->writePage(currBufDesc.pageNo, &(bufPool[clockHand]));
                    if (currStatus != OK)
                    {
                        return UNIXERR;
                    }
                }
                found = true;
                break;
            }
        }
    }

    // if we haven't found a frame after two cycles, return BUFFEREXCEEDED. otherwise, we can prepare the frame for use
    if (!found)
    {
        return BUFFEREXCEEDED;
    }

    Status hashStatus = OK;
    if ((hashStatus = hashTable->lookup(bufTable[clockHand].file, bufTable[clockHand].pageNo, bufTable[clockHand].frameNo)) == OK)
    {
        hashTable->remove(bufTable[clockHand].file, bufTable[clockHand].pageNo);
    }

    bufTable[clockHand].Clear();
    frame = clockHand;
    return currStatus;
}
/**
 * @brief method to read a page from the database or the buffer if the page is already stored in the memory
 *
 * @param file the file to read the page from
 * @param PageNo the page number within the file that the page is located in
 * @param page pointer to the page so that the user can read what is stored in the page
 * @return const Status status of the method returning OK when it is successfully read
 */
const Status BufMgr::readPage(File *file, const int PageNo, Page *&page)
{
    int frameIndex = 0;
    Status currStatus;

    // if requested page already in buffer pool (or hash table), set reference bit to true,increment pin count, and set page pointer to frame
    if ((currStatus = hashTable->lookup(file, PageNo, frameIndex)) == OK)
    {
        bufTable[frameIndex].refbit = true;
        bufTable[frameIndex].pinCnt++;
        page = &bufPool[frameIndex];
    }
    else
    {
        // call allocBuf to allocate a buffer frame
        if ((currStatus = allocBuf(frameIndex)) != OK)
        {
            return currStatus;
        }

        // call readPage() to read page from disk into buffer pool frame
        if ((currStatus = file->readPage(PageNo, &bufPool[frameIndex])) != OK)
        {
            return currStatus;
        }

        // insert page into hashTable
        if ((currStatus = hashTable->insert(file, PageNo, frameIndex)) != OK)
        {
            return currStatus;
        }

        // invoke Set() on frame
        bufTable[frameIndex].Set(file, PageNo);

        // set page pointer to frame
        page = &bufPool[frameIndex];
    }

    return currStatus;
}
/**
 * @brief decrease the pin count to let the system know that the user is no longer accessing the page
 *
 * @param file the file that the page resides in
 * @param PageNo the page number within the file for the corresponding page
 * @param dirty a bool value that shows whether the file has been edited
 * @return const Status returns OK if successfully unpinned the page
 */
const Status BufMgr::unPinPage(File *file, const int PageNo,
                               const bool dirty)
{
    int frameIndex = 0;
    Status currStatus = OK;

    // return HASHNOTFOUND if page not in buffer pool
    if ((currStatus = hashTable->lookup(file, PageNo, frameIndex)) != OK)
    {
        return currStatus;
    }

    // return PAGENOTPINNED if pin count already 0
    if (bufTable[frameIndex].pinCnt == 0)
    {
        return PAGENOTPINNED;
    }

    bufTable[frameIndex].pinCnt--;

    if (dirty)
    {
        bufTable[frameIndex].dirty = true;
    }

    return currStatus;
}
/**
 * @brief allocates an empty page for the user to write in
 *
 * @param file the file that the empty page is being created in
 * @param pageNo the variable that the new page number is stored in
 * @param page pointer to the page that is being created
 * @return const Status returns OK if method successfully creates and allocated new page
 */
const Status BufMgr::allocPage(File *file, int &pageNo, Page *&page)
{
    int frameIndex = 0;
    Status currStatus;
    // allocate an empty page in the file with allocatePage()
    if ((currStatus = file->allocatePage(pageNo)) != OK)
    {
        return currStatus;
    }

    // call allocBuf() to obtain buffer pool frame
    if ((currStatus = allocBuf(frameIndex)) != OK)
    {
        return currStatus;
    }

    // insert entry into hash table
    if ((currStatus = hashTable->insert(file, pageNo, frameIndex)) != OK)
    {
        return currStatus;
    }

    // invoke Set() on frame
    bufTable[frameIndex].Set(file, pageNo);
    page = &bufPool[frameIndex];

    return currStatus;
}

const Status BufMgr::disposePage(File *file, const int pageNo)
{
    // see if it is in the buffer pool
    Status status = OK;
    int frameNo = 0;
    status = hashTable->lookup(file, pageNo, frameNo);
    if (status == OK)
    {
        // clear the page
        bufTable[frameNo].Clear();
    }
    status = hashTable->remove(file, pageNo);

    // deallocate it in the file
    return file->disposePage(pageNo);
}

const Status BufMgr::flushFile(const File *file)
{
    Status status;

    for (int i = 0; i < numBufs; i++)
    {
        BufDesc *tmpbuf = &(bufTable[i]);
        if (tmpbuf->valid == true && tmpbuf->file == file)
        {

            if (tmpbuf->pinCnt > 0)
                return PAGEPINNED;

            if (tmpbuf->dirty == true)
            {
#ifdef DEBUGBUF
                cout << "flushing page " << tmpbuf->pageNo
                     << " from frame " << i << endl;
#endif
                if ((status = tmpbuf->file->writePage(tmpbuf->pageNo,
                                                      &(bufPool[i]))) != OK)
                    return status;

                tmpbuf->dirty = false;
            }

            hashTable->remove(file, tmpbuf->pageNo);

            tmpbuf->file = NULL;
            tmpbuf->pageNo = -1;
            tmpbuf->valid = false;
        }

        else if (tmpbuf->valid == false && tmpbuf->file == file)
            return BADBUFFER;
    }

    return OK;
}

void BufMgr::printSelf(void)
{
    BufDesc *tmpbuf;

    cout << endl
         << "Print buffer...\n";
    for (int i = 0; i < numBufs; i++)
    {
        tmpbuf = &(bufTable[i]);
        cout << i << "\t" << (char *)(&bufPool[i])
             << "\tpinCnt: " << tmpbuf->pinCnt;

        if (tmpbuf->valid == true)
            cout << "\tvalid\n";
        cout << endl;
    };
}
