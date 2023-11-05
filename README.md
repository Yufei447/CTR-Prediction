# CTR-Prediction
Advertising Analytics Click-Through Rate (CTR) Prediction via Wide&amp;Deep                                                                                                      

The dataset can be found at https://www.kaggle.com/c/avazu-ctr-prediction. For this project, I use a truncated version of the data using random sampling, comprising approximately 40,000 records. 

The explorative data analysis is conducted within the file EDA_spark sql.ipynb by analyzing the correlation between the features and the response. As can be seen from the analysis, there are some essential features that are correlated with the response rate. Consequently, I designed the cross-product feature transformations for these features.

I further manually designed the Dataset class and use PyTorch.DataLoader to load data per batch for traning and evaluating. 

I firstly designed the Wide & Deep model and then built its variations Deep & Cross and DeepFM. However, w.o. manually designing feature interaction, they have poor performance on this dataset.



