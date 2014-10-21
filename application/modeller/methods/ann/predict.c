#include <stdio.h>
#include "fann.h"
	
int main(int argc, char **argv)
{
	printf("%s", *(argv +1));
	if (*(argv + 1) != NULL)
	{
		if ((strncmp(*(argv + 1), "-h") != 0) && ((strncmp(*(argv + 1), "-help") != 0)))
		{
			printf("\nprogram args:\n  -  [path to network_file] [input1 input2 input3 ...] \n  -  [-h/-help] - display help");
			return 1;
		}
	}
	printf("Profile : %s\n", *(argv + 1));
	int arg_num = 2;
	printf("Prediction input :"); 
	while (*(argv + arg_num))
	{
		printf(" %s", *(argv + arg_num));
		arg_num++;
	}
	arg_num = arg_num - 2;
	printf("\n");
	
	struct fann *ann = fann_create_from_file(*(argv + 1));
	fann_type *calc_out;
    fann_type input[arg_num];
    
    // parse again the arguments to get the input for the network
    arg_num = 0;
    while (*(argv + arg_num + 2))
	{
		input[arg_num] = atof(*(argv + arg_num + 2));
		arg_num++;
	}
    
    printf("\n");
    
    calc_out = fann_run(ann, input);
	printf("Result: %f\n", calc_out[0]);
    //printf("predict test (%f,%f,%f) -> %f\n", input[0], input[1], input[2], calc_out[0]);
    fann_destroy(ann);
    
    return 0;
}
    
