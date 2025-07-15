# Task 4: Creating a Dashboard for Analysis / Visualization

## Overview

Task 4 focused on enhancing the visualization dashboard built in previous tasks by incorporating detailed analytical features, adherence tracking, data imputation methods, and participant management capabilities.

## Technical Implementation

### Frontend Dashboard Enhancements

* Expanded on the existing React.js frontend, adding multiple advanced analysis and visualization features:

  * **Adherence Overview:**

    * Displays whether participants have an active token.
    * Tracks the timestamp of the last data upload, highlighting when no data has been uploaded in the last 48 hours.
    * Monitors sleep upload percentages based on configurable thresholds.
    * Calculates wear-time adherence, with alerts when adherence drops below 70%.

* Integrated a dynamic participant list for simplified navigation, though currently, only the first participant has functional synthetic data due to dataset limitations.

### Data Imputation Method

* Implemented a robust data imputation algorithm for managing missing data after study periods conclude, going beyond basic interpolation methods (mean/median).
* Each imputed value is explicitly tracked, enabling clear differentiation and analysis with or without imputed values. On the frontend it displays imputed data as red and regular as blue.
* Currently there is a known bug with data imputation. While I believe the imputed data is being tracked correctly internally, it is displaying wrong on the frontend sometimes, where it shows all the data as imputed, instead of just what is actually imputed.

### Communication Feature

* Built functionality enabling the dashboard to have a button to send email alerts to participants whose adherence falls below defined thresholds, facilitating proactive participant engagement and study compliance. The button only pops up when the threshhold is reached. 
* To test this pick a date in the graph that way is past where the synthetic data ends (1/30/2024). This makes it so the adherence falls and you can test out the button to send the email notification.

### Schema Details

No additional database schema changes were required; all enhancements leveraged existing data structures from previous tasks.

## Key Decisions & Justifications

### Enhanced Adherence Tracking

* Developed to proactively identify and address participant compliance issues, critical in maintaining data integrity and reliability for clinical trials.

### Advanced Imputation Method

* Chosen to ensure comprehensive and reliable data for analysis, allowing robust statistical analysis and reliable visualization despite data gaps.

### Email Notifications

* Implemented to streamline researcher-participant communication, increasing overall compliance and reducing administrative workload.
* Emails and SMTP implementation are represented with Mailhog. 

### Known Issues

* **Imputed Data Bug:**

  * Occasionally, the graphical representation incorrectly marks non-imputed data points (blue) as imputed (red). Investigation and resolution of this visual bug are recommended for accurate user experience.

* **Participant Data Limitation:**

  * Currently, only Participant 1 is fully functional due to synthetic dataset limitations. Expanding the synthetic dataset will improve comprehensive testing and demonstration.

* **Timestamp Display Issue:**

  * Displays "last uploaded over a year ago" due to the static nature of the synthetic dataset from January 2024, which should be clarified or dynamically adjusted for real datasets.

## Configuration & Usage

### Running the Dashboard

To launch the dashboard application, execute:

```sh
docker-compose up
```

### Dashboard Features

* Navigate to `http://localhost:3000` to interact with the enhanced dashboard.
* Selectable metrics (e.g., Heart Rate (HR), steps).
* Adherence indicators visible on participant selection.
* Email notification triggered automatically when adherence metrics fall below set thresholds.

### Imputation Tracking

* The imputation status of each data point is visually represented, albeit with a known intermittent visual issue that should be prioritized for resolution.

## Possible Next Steps

* Resolve graphical bug relating to imputed data representation.
* Expand synthetic data for comprehensive participant visualization.