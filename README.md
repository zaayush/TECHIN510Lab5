## TECHIN510Lab5
A interactive data visualization app for events in Seattle  

## How to Run
Open the terminal and run the following commands:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Or just go the link : [Seattle Events Data Visualization](aayushlab5.azurewebsites.net)

## What's Included

- `app.py`: The main application made with streamlit.
- `scraper.py`: The scraper application to scrape data from Seattle Events website.

## Lessons Learned

- How to make use altair for creating Data Visualizations
- How to use postgres and connect to or app.
- How to create multiple deployement environments, use secret variables in github actions and Azure.

## Questions / Uncertainties

- How to store/edit/update data in postgress from the streamlit app interface (app.py)?