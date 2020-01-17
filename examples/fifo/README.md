FIFO in Peak

ILA example

ringbuffer.c
- ring buffer from cs107e

Tricky parts of hardware. 
- Simultaneous enqueue and dequeue
- Crossing clock domains

A FIFO implemented wqith An n-bit counter can only hold N-1 values.

Trick is to use an (N+1)-bit counter. Then can hold N values.
- see Cummings article in doc
- https://zipcpu.com/blog/2018/07/06/afifo.html

Formal Properties

1. assert fifo.fill() < N
if fifo.fill() == N-1:
    ASSERT((next(full_next)||(!i_wr)||(o_wfull));
2. if fifo.fill() == 0: assert(fifo.empty())
if fifo.fill() == 1:
    ASSERT(...)
3. if fifo.fill() == N: assert(fifo.full())

See https://www.techdesignforums.com/practice/technique/doc-formal-harness-the-power-of-invariant-based-bug-hunting/
No data lost
No data reordering
No data duplication


