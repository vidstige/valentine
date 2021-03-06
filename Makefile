main: main.c solver.c solver.h image.c
	gcc -Wall main.c solver.c image.c -o main 
	#-Werror 

run: main
	./main | ./stream.sh