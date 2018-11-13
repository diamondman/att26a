import queue

"""Code based on Carl Banks' excellent work for python 2.5 from
http://code.activestate.com/recipes/576461-interruptible-queue/

This Queue modification is used to enable interrupting threads that
are listening for buttons from the 26A when the driver is being shut
down. The alternative is requiring all reads from the button queue to
have a timeout so the respective threads can check if they should loop
again.

"""

class QueueInterruptException(Exception):
    pass

class InterruptableQueue(queue.Queue):
    """Subclass of Queue allows one to interrupt consumers."""

    def __init__(self,maxsize=0):
        queue.Queue.__init__(self,maxsize)
        self.consumer_interrupt = False

    def interrupt_all_consumers(self):
        """Raise QueueInterrupt in all consumer threads.

        Any thread currently waiting to get an item, and any subsequent thread
        that calls the get() method, will receive the QueueInterrupt exception.

        """
        self.not_empty.acquire()
        self.consumer_interrupt = True
        self.not_empty.notifyAll()
        self.not_empty.release()

    def _empty(self):
        if self.consumer_interrupt:
            return False
        return queue.Queue._empty(self)

    def _get(self):
        if self.consumer_interrupt:
            raise QueueInterruptException()
        return queue.Queue._get(self)

    def _qsize(self):
        if self.consumer_interrupt:
            return 1 # break loop in get()!
        return queue.Queue._qsize(self)
