class FIFO:
    def __init__(self, loglength):
        self.length = (1<<loglength)
        self.mem = self.length * [0]
        self.reset()

    def reset(self):
        self.wraddr = 0
        self.rdaddr = 0

    def empty(self):
        return self.wraddr == self.rdaddr

    def full(self):
        nextaddr = self.wraddr + 1
        if nextaddr >= self.length:
            nextaddr = 0
        return nextaddr == self.rdaddr

    # Write/produce an item 
    def write(self, item):
        nextaddr = self.wraddr + 1
        if nextaddr >= self.length:
            nxtaddr = 0

        if nextaddr != self.rdaddr:
            # Actually write an item to the FIFO
            self.mem[self.wraddr] = item
            self.wraddr = nextaddr

    # Read/consume one item 
    def read(self):

        item = self.mem[self.rdaddr]

        # Only consume if the FIFO is not empty
        if self.rdaddr != self.wraddr:
            self.rdaddr += 1;
            if self.rdaddr >= self.length:
                self.rdaddr = 0;

        return item
