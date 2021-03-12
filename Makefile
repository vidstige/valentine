CC      := gcc
BIN     := ./bin
OBJ     := ./obj
INCLUDE := ./include
SRC     := ./src
SRCS    := $(wildcard $(SRC)/*.c)
OBJS    := $(patsubst $(SRC)/%.c,$(OBJ)/%.o,$(SRCS))
BINARY  := smoked-heart
CFLAGS  := -I$(INCLUDE) -Wall -Werror -pedantic
LDLIBS  :=

.PHONY: all run clean

all: $(BINARY)

$(BINARY): $(OBJS)
	$(CC) $(LDFLAGS) $^ -o $@ $(LDLIBS)

$(OBJ)/%.o: $(SRC)/%.c | $(OBJ)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ):
	mkdir $@

run: $(BINARY)
	./$< | ./stream.sh

test: $(BINARY) expected
	./$< > actual
	diff expected actual

clean:
	rm -r $(OBJ) $(BINARY)
