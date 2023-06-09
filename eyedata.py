# -*- coding: utf-8 -*-
"""eyedata.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1d0XkdwIR5Kslggeqa8FAl2cIo97ZoTQF
"""

from google.colab import drive
drive.mount('/content/drive', force_remount= True)

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
# %matplotlib inline
sns.set_theme()
import warnings
warnings.filterwarnings('ignore')
#!pip install tabula-py
from tabula import read_pdf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error,explained_variance_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.linear_model import SGDRegressor

train_df = pd.read_csv('/content/drive/MyDrive/Eye empathy/test_merged.csv')
train_df.head()

#importing the first questionnaire
ques1 = pd.read_csv('/content/drive/MyDrive/Eye empathy/Questionnaire_datasetIA.csv', encoding = 'latin-1' )

#columns and what they represent 
#column_meanings = read_pdf('/content/drive/MyDrive/EYET4EMPATHY /columns_explained.pdf', encoding= 'latin-1', stream = True, pages= 'all')
#column_meanings[0]

"""#EDA/Data Cleaning"""

#visualizing sparseness of the first 25 features
#sns.heatmap(train_df_subset.iloc[:,:25].isnull(), cbar = False)

#visualizing sparsity of the remaining of the remaining features 
#sns.heatmap(train_df_subset.iloc[:,25:].isnull(), cbar = False)

"""Features that will be dropped due to high percentage of null values:

Mouse position Y 

Mouse position X 

Event 

Event Value 

Unnamed: 0 will be dropped because it emerged from the merging of the datasets.

Recording Timestamp is just a unique identifier and will not be of use to the predictions here. Computer Timestamp will also not be of any applicable usage in the predictions.






"""

#selecting the subset of the data that has the pupil dilations to be non-null values
train_df_subset = train_df[(train_df['Pupil diameter left'].notnull()) & (train_df['Pupil diameter right'].notnull())]
train_df_subset

train_df_subset['Sensor'].value_counts()

"""The feature 'Sensor' which represents the sensor type used in the data gathering is greatly imbalanced and also won't be of use to HR in empathy assessment during interviews. """

train_df_subset['Participant name'].unique()

"""The participant names can be engineered to extract the participant number will then be used to assign the empathy scores from the questionnaire dataset. Rows having participant name as 'participant name' wil be dropped because there is no alternative method of assigning the empathy scores to them. """

train_df_subset.drop(train_df_subset[train_df_subset['Participant name'] == 'Participant name'].index, inplace = True)

#function to extract the id from the participant name
def id(num):
  if type(num) is str:
    c = list(num)
    d = int(''.join(c[-2:]))
    return d
  else:
    return 'NaN'
train_df_subset['id'] = train_df_subset['Participant name'].apply(id)

train_df_subset['id'].value_counts()

train_df_subset[['Recording start time', 'Recording start time UTC', 'Eyetracker timestamp']]

"""The first two features above contain the same timestamp but using different time regions. The model training on this two features will be detrimental. 

The eyetracker timestamp rather, is the time elapsed in seconds. 
"""

train_df_subset[['Presented Media name', 'Presented Stimulus name' ]].head(10)

"""They contain same data and both are not useful for training the model. """

#dropping features deemed not to be useful
train_df_subset.drop(['Sensor', 'Recording timestamp','Computer timestamp','Export date', 'Participant name', 'Recording name', 'Recording date', 'Timeline name', 'Recording Fixation filter name','Mouse position X', 'Mouse position Y', 'Recording software version','Event', 'Event value', 'Project name','Presented Media name', 'Presented Stimulus name', 'Unnamed: 0','Eyetracker timestamp','Recording start time UTC', 'Recording date UTC','Project name'], axis = 1, inplace = True)

train_df_subset.drop(['Gaze point X (MCSnorm)', 'Gaze point Y (MCSnorm)', 'Gaze point left X (MCSnorm)', 'Gaze point left Y (MCSnorm)', 'Gaze point right X (MCSnorm)', 'Gaze point right Y (MCSnorm)', 'Fixation point X', 'Fixation point Y','Fixation point X (MCSnorm)','Fixation point Y (MCSnorm)'], axis = 1,  inplace = True)

"""Many columns will be dropped due to high sparsity. This is because there are more null values than not in those columns and a mean/average input to fill the null values could cause a bias in the predictions.

Fixation point X (MCSnorm) and Fixation point Y (MCSnorm) will be dropped because of their sparsity. This rows represent normalized coordinates, creating random ones could be detrimental to the model training. 

The normalized coordinates (MSCnorm) for gaze points x and y (both right and left) will be dropped also for similar reasons.
"""

train_df_subset.head()

train_df_subset['Eye movement type'].value_counts()

#manual label encoding of the train_df['Eye movement type'] column 
dict_eye = {'Fixation': round(0), 'Saccade': round(1), 'Unclassified': round(2), 'EyesNotFound':round(3) }
train_df_subset['Eye movement type'] = ([dict_eye.get(i) for i in train_df_subset['Eye movement type']])
train_df_subset['Eye movement type'] = train_df_subset['Eye movement type'].astype(str)
train_df_subset['Eye movement type'].value_counts()

#sns.heatmap(train_df_subset.iloc[:,:25].isnull(), cbar = False)

#sns.heatmap(train_df_subset.iloc[:,25:].isnull(), cbar = False)

print(train_df_subset['Recording resolution height'].value_counts(), '\n', train_df_subset['Recording resolution width'].value_counts(), '\n',train_df_subset['Recording monitor latency'].value_counts())

"""They contain same values throughout so they will be dropped. """

train_df_subset.drop(['Recording resolution height', 'Recording monitor latency','Recording start time', 'Recording resolution width'], axis = 1, inplace = True)

train_df_subset.drop(['Validity right','Validity left'], axis = 1, inplace = True)

"""Trying to convert columns to float """

def conv(mm):
  if type(mm) is not float and type(mm) is not int:
    if ',' in mm:
      mm = float(mm.replace(',','.'))
      return mm 
    else: 
      mm = float(mm)
      return mm 
  else:
    return mm



for i in train_df_subset.columns:
  if i != 'Eye movement type'  and i != 'id':
    train_df_subset[i] = train_df_subset[i].apply(conv)

train_df_subset.info()

#mapping the participant empathy scores to their id 
dict_ = dict(zip(ques1['Participant nr'], ques1['Total Score original']))
#adding the empathy scores extracted from the questionnaire dataset to the subset of the train_df group dataset
train_df_subset['Empathy scores'] = [dict_.get(i) for  i in train_df_subset.id]
#dropping the id because it will be of no use after mapping the scores to the data
train_df_subset.drop('id',axis=1,inplace = True)
train_df_subset.reset_index(drop = True, inplace = True)
train_df_subset.dropna(inplace = True)

train_df_subset.head()

X_train = train_df_subset.drop('Empathy scores', axis = 1)
y_train = train_df_subset['Empathy scores']

"""DATA CLEANING AND FEATURE SELECTION ON THE test GROUP """

test = pd.read_csv('/content/drive/MyDrive/Eye empathy/merged_control.csv')
test.head()

test['Eye movement type'].value_counts()

#creating a list of feature names from the training data subset
cols = train_df_subset.columns
#creating a subset of the data using non-null pupil diameters as criteria
test_subset = test[(test['Pupil diameter left'].notnull()) & (test['Pupil diameter right'].notnull())]
#removing rows that have the value 'Participant name' for the 'Participant name' column
test_subset.drop(test_subset[test_subset['Participant name'] == 'Participant name'].index, inplace = True)
#creating id column from participant names using the function defined during training
test_subset['id'] = test_subset['Participant name'].apply(id)
#encoding the eye movement type column 
test_subset['Eye movement type'] = [dict_eye.get(i) for i in test_subset['Eye movement type']]
test_subset['Eye movement type'] = test_subset['Eye movement type'].astype(str)
#mapping  empathy scores to identity
test_subset['Empathy scores'] = [dict_.get(i) for  i in test_subset.id]
#selecting the feature names from the training subset
test_subset = test_subset[cols]
#converting string data to float
for i in test_subset.columns:
  if i != 'Eye movement type'  and i != 'id':
    test_subset[i] = test_subset[i].apply(conv)
test_subset.reset_index(inplace = True, drop = True)

#dropping null values
test_subset.dropna(inplace = True)
test_subset.shape

X_test = test_subset.drop('Empathy scores',axis = 1)
y_test = test_subset['Empathy scores']
X_test= X_test.reset_index(drop=True)

scaler = StandardScaler()
scaled_Xtrain = pd.DataFrame(scaler.fit_transform(X_train.drop('Eye movement type', axis = 1)))
scaled_Xtrain['Eye movement type'] = X_train['Eye movement type']
scaled_Xtest = pd.DataFrame(scaler.transform(X_test.drop('Eye movement type', axis = 1)))
scaled_Xtest['Eye movement type'] = X_test['Eye movement type']

scaled_Xtest.shape

#model  initialization 
rfc = RandomForestRegressor(random_state = 2)
#fitting the model to the training data
rfc.fit(X_train,y_train)
#predicting the empathy scores on the test set
y_pred = np.around(rfc.predict(X_test))
#evaluating the model
print('Training Score:', rfc.score(X_train,y_train))
print('MAE: ', mean_absolute_error(y_test, y_pred))
print('RMSE: ',mean_squared_error(y_test, y_pred, squared= False))
print('Explained Variance Score:',explained_variance_score(y_test, y_pred))

#visualizing the model's prediction accuracy 
#creating a scatterplot of the values
plt.scatter(y_test,y_pred,cmap = 'viridis')
#drawing a line of best fit
plt.plot (np.unique (y_test), np.poly1d (np.polyfit (y_test,y_pred, 1))(np.unique (y_test)), color = 'green') 
#adding titles and labels 
plt.title('LinearRegressor Accuracy')
plt.xlabel('Original Empathy Scores')
plt.ylabel('Predicted Empathy Scores')
plt.show()

from sklearn.linear_model import LinearRegression
lr = LinearRegression()
lr.fit(X_train,y_train)
y_pred = lr.predict(X_test)
#evaluating the model 
print('Training Score:', lr.score(X_train,y_train))
print('MAE: ', mean_absolute_error(y_test, y_pred))
print('RMSE: ',mean_squared_error(y_test, y_pred, squared= False))
print('Explained Variance Score:',explained_variance_score(y_test, y_pred))

output_test = pd.DataFrame(y_test)
output_test['Predicted Empathy Score'] = y_pred
output_test.tail(10)

#visualizing the model's prediction accuracy 
#creating a scatterplot of the values
plt.scatter(y_test,y_pred,cmap = 'viridis')
#drawing a line of best fit
plt.plot (np.unique (y_test), np.poly1d (np.polyfit (y_test,y_pred, 1))(np.unique (y_test)), color = 'green') 
#adding titles and labels 
plt.title('LinearRegressor Accuracy')
plt.xlabel('Original Empathy Scores')
plt.ylabel('Predicted Empathy Scores')
plt.show()