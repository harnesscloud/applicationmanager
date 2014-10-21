#include <Python.h>
#include "fann.h" 
#include <stdio.h>


 
struct fann * _create(const unsigned int num_layers, unsigned int* topology)
 {
	 
	const fann_type min_weight = -0.2;
	const fann_type max_weight = 0.2;
	
 	//create network
    struct fann *ann = fann_create_standard_array(num_layers, topology);
    
    //fann_set_training_algorithm(ann, FANN_TRAIN_QUICKPROP);
    fann_set_training_algorithm(ann, FANN_TRAIN_RPROP);
    
    fann_set_activation_function_hidden(ann, FANN_LINEAR);
    fann_set_activation_function_output(ann, FANN_LINEAR);
    fann_randomize_weights(ann, min_weight, max_weight);
	fann_set_learning_momentum(ann,0.03);
 	fann_set_learning_rate(ann, 0.9);
    fann_print_connections(ann);

 	fann_get_training_algorithm(ann);
 
 	printf("OK");
 	
 	//printf("\n\n\n PARAMETRII RETEA creare\n\n");
 	//fann_print_parameters(ann);
 	//printf("\n\n\n");
 	return ann;
 }
 
 
static unsigned int* get_ann_topology(PyObject* data, unsigned int* data_size)
{
    int i, size;
    unsigned int* out;
    PyObject* seq;

    seq = PySequence_Fast(data, "expected a sequence");
    if (!seq)
        return NULL;

    size = PySequence_Size(seq);
    
    printf("Seq size :%d" , size);
    if (size < 0)
        return NULL;

    if (data_size)
        *data_size = size;

    out = (unsigned int*) PyMem_Malloc(size * sizeof(unsigned int));
    if (!out) {
        Py_DECREF(seq);
        PyErr_NoMemory();
        return NULL;
    }

    for (i = 0; i < size; i++)
        out[i] = PyInt_AsLong(PySequence_Fast_GET_ITEM(seq, i));
    Py_DECREF(seq);

    if (PyErr_Occurred()) {
        PyMem_Free(out);
        out = NULL;
    }

    return out;
}
 
 
static PyObject*
create(PyObject* self, PyObject* args)
{
	printf("\n~C~ Creating a Neural Network.\n");

	unsigned int num_layers = 2;
 	unsigned int* topology;
	
	PyObject* vals_in;
	 	
    if (!PyArg_ParseTuple(args, "O:create", &vals_in))
        return NULL;
        
 	topology = get_ann_topology(vals_in, &num_layers);
    if (!topology)
        return NULL;
        
     /* do stuff */
    int i;
    printf("\n~ Topology ~\n");
    for (i = 0; i < num_layers; i++)
        printf("%u ", topology[i]);
    printf("\n");
        
    struct fann *ann = _create(num_layers, topology);
    //save network in file
    //fann_save(ann, "/tmp/ann.net");
    //printf("\n~C~ Done.\n");
    
    PyObject *capsula = PyCapsule_New((void*)ann, "ann", NULL);
	return capsula;
    //Py_RETURN_NONE;
}






struct fann * _train(struct fann* ann, char* file)
 {
	 		 
	const float desired_error = (const float) 10.000;
	const unsigned int max_epochs = 100;
	const unsigned int epochs_between_reports = 10;
	
	//train network	
 	
    fann_train_on_file(ann, file, max_epochs, epochs_between_reports, desired_error);
    
    //save network in file
    fann_save(ann, "/tmp/retea.net");
 	return ann;
 }
 
 
 

static PyObject * train(PyObject* self, PyObject* args)
{
 	char* data_file;
 	PyObject *capsula;
    PyArg_ParseTuple(args, "Os", &capsula, &data_file);
    
    printf("\nTraining the neural network\n");
    
    struct fann *ann = (struct fann *)PyCapsule_GetPointer(capsula,"ann");
    
    ann = _train(ann, data_file);
   
   	PyObject *result = PyCapsule_New((void*)ann, "ann", NULL);
	
	return result;
}


 

static double* get_input_set(PyObject* data, unsigned int* data_size)
{
    int i, size;
    double* out;
    PyObject* seq;

    seq = PySequence_Fast(data, "expected a sequence");
    if (!seq)
        return NULL;

    size = PySequence_Size(seq);
    
    if (size < 0)
        return NULL;

    if (data_size)
        *data_size = size;

    out = (double*) PyMem_Malloc(size * sizeof(double));
    if (!out) {
        Py_DECREF(seq);
        PyErr_NoMemory();
        return NULL;
    }

    for (i = 0; i < size; i++)
        out[i] = PyFloat_AsDouble(PySequence_Fast_GET_ITEM(seq, i));
    Py_DECREF(seq);

    if (PyErr_Occurred()) {
        PyMem_Free(out);
        out = NULL;
    }

    return out;
}





 double _predict(struct fann * ann, fann_type* input)
 {
 	fann_type *calc_out;   
 	//ann = fann_create_from_file("/tmp/retea.net");
 	
 	int num = 0;
 	printf("Input :");
 	while (*(input + num))
	{
		printf(" %f", *(input + num));
		num = num  +1;
	}
    calc_out = fann_run(ann, input);
	printf("Predicting Result: %f\n", calc_out[0]);
   	return calc_out[0];
 }
 

static PyObject*
predict(PyObject* self, PyObject* args)
{
	unsigned int num;
	
	PyObject* vals_in;
	double* vals_out;
	
	PyObject* capsula;
	
    if (!PyArg_ParseTuple(args, "OO:predict",&capsula, &vals_in))
        return NULL;
        
 	vals_out = get_input_set(vals_in, &num);
    if (!vals_out)
        return NULL;
        
    int i;
    
    fann_type input[num];
    printf(" Num =%u",num);
    for (i = 0; i < num; i++)
    {    
        input[i] = vals_out[i];
    }
    printf("\n");
    
    
    struct fann *ann = (struct fann *)PyCapsule_GetPointer(capsula,"ann");
    
	float result = _predict(ann, input);
    
    //printf("Return from predict.");
    return Py_BuildValue("d", result);
}





 
 void _destroy(void)
 {
 	//fann_destroy(ann);
 }

static PyObject * destroy(PyObject* self, PyObject *args)
{
    _destroy();
    Py_RETURN_NONE;
}


 
static PyMethodDef ANNMethods[] = {
    {"create", create, METH_VARARGS, "Create a neural network."},
    {"train", train, METH_VARARGS, "Train the neural network."},
    {"predict", predict, METH_VARARGS, "Predict the output."},
    {"destroy", destroy, METH_VARARGS, "Destroy the neural network."},
    {NULL, NULL, 0, NULL},
};

 
 
 
PyMODINIT_FUNC
initneuralnetwork(void)
{
    (void) Py_InitModule("neuralnetwork", ANNMethods);
}


