# End to End RAG System

We have implemented a RAG system over content related to pittsburgh and CMU.

## Data Preparation

The main file responsible for crawling data from the web is `crawling/crawler.py`. This files crawls content from a specific set of urls, processes the content and stores it in `crawling/scraped_data`  .

## Model

All the code related to our model lies in the `ipynb` notebooks in the `model` folder. The ipynb notebook `model/vector_db_creator.ipynb` creates and stores our vectors database. The notebook `model/model.ipynb` contains all the modeling and inference code. It loads the vector db and runs all the inference logic. It also has the residues of our previous runs(model2.ipynb is a copy of model.ipynb and was also used for generating results). The ideal way to reproduce our results is to attach these notebooks to collab and then run them.

## Test Data

Our test data lies in the folder `test_data`. It has both questions and the ground truth answers.

## Evaluation

To evaluate the ouptuts of our models we can use `evaluation.py` which generates the  f1, recall, precision values and exact match based on the ground truth answers. An example usage is `python evaluate/evaluation.py answers_flashrerank.txt test_data/reference_answers.tx`

Similarly to calculate the statistical significance of our model, we can use `bootstrap_sampling.py`.

### IAA

The annotation used for calculating iaa are stored in this folder. To get the values for this, we can use the evaluation script on these annotations.
