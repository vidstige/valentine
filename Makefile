main: main.c solver.c solver.h
	gcc -Wall main.c solver.c -o main 
	#-Werror 

run: main
	./main | ./stream.sh