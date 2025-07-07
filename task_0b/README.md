\# Task 0 b: Synthetic Fitbit Data Extraction



This folder contains 30 days of "synthetic" Fitbit Charge 6 intraday data

(2024-01-01 → 2024-01-30) for one participant.









---



\## How the data was generated



1\. \*\*Opened the official Wearipedia notebook\*\*  

&nbsp;  <https://colab.research.google.com/github/Stanford-Health/Wearible-notebooks/blob/main/notebooks/fitbit\_charge\_6.ipynb>



2\. \*\*Enabled `synthetic` mode\*\* (Section 2) 



3\. \*\*Ran Section 3 `Data Extraction`\*\* to create six Python variables  

&nbsp;  (`heart\_rate\_day`, `intraday\_activity\_day`, …).



4\. \*\*Exported each variable to CSV\*\* in the Colab session.



5\. \*\*Zipped \& downloaded\*\* the six CSV files (`files.download`).



6\. \*\*Converted CSV to Parquet\*\* locally for smaller size \& typed columns

