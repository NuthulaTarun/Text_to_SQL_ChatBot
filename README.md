# Google Marketing Analytics Bot

![Python Version](https://img.shields.io/badge/python-3.11.7-blue)

## 📚 Overview

**Google Marketing Analytics Bot** is a Streamlit application designed for marketing professionals to interact with and receive forecasting, optimization, and analytics insights through a conversational interface. Built with **Python 3.11.7**, it primarily utilizes the `LangChain` library and integrates with Google Cloud components such as `BigQuery`, `Vertex AI`, and the `Claude Connect 3.5` LLM.

The CI/CD pipeline is implemented using `Google Cloud Build` and the application is deployed as a `Google Cloud Run` service.

## 📂 Project Structure

```
    └── 📁google-marketing-analytics-bot
        ├── 📄 .streamlit                             # Configuration for Streamlit app's appearance.
        ├── 📄 images                                 # Contains images and logos used in the project.
        ├── 📁pages
            ├── 📄 chatwindow.py                      # Frontend code for the chat interface.
        ├── 📁src
            ├── 📁chains
                ├── 📄 IntentRecognitionChain.py      # Classifies user queries into different intents.
                ├── 📄 NLResponseChain.py             # Generates NLP responses based on SQL results.
                ├── 📄 PlotColumnsChain.py            # Determines columns for plotting based on user and SQL response.
                ├── 📄 SQLGenChain                    # Generates SQL queries from user inputs.
                ├── 📄 StandaloneChain                # Generates standalone questions using user query and chat history.
            ├── 📁chatbot_ui
                ├── 📄 chat_ui.py                     # Code for displaying chat messages.
                ├── 📄 streamlit_app.py               # Authentication code for the Streamlit app.
            ├── 📁examples
                ├── 📄 few_shot_queries.json          # Example SQL queries for few-shot learning.
                ├── 📄 intent_trial.json              # Example data for intent classification.
            ├── 📁MLModels
                ├── 📄 forecasting.py                 # Code for forecasting models.
                ├── 📄 optimization.py                # Code for optimization models.
            ├── 📁prompts
                ├── 📄 nlresponse_prompt.txt          # Prompt template for NLP response generation.
                ├── 📄 nlresponseMLmodel_prompt.txt   # NLP Response ml model prompt.
                ├── 📄 plotcolumns_prompt.txt         # Plotly express plot columns prompt.
                ├── 📄 sqlgen_prompt.txt              # Sql generation prompt
                ├── 📄 standalone_prompt.txt          # Standalone prompt
                ├─  📄 userintent_prompt.txt          # User intent prompt
            ├── 📁utils
                ├── 📄 bigqueryutils.py               # Helper functions for BigQuery operations.
                ├── 📄 chartutils.py                  # Functions for chart plotting.
                ├── 📄 chatutils.py                   # Functions for processing user queries and generating responses.
                ├── 📄 constants.oy                   # Constants used throughout the project.
                ├── 📄 llmutils.py                    # Helper functions for defining LLM models.
                ├── 📄 snowflakeutils.py              # Helper functions for Snowflake operations.
                ├── 📄 sqlutils.py                    # Functions for SQL query correction.query.                                                    
        ├── 📄 app.py                                 # Main entry point of the application.
        ├── 📄 cloudbuild.yml                         # CI/CD configuration for Google Cloud Build.
        ├── 📄 credentials.json                       # GCP credentials for service authentication.
        ├── 📄 Dockerfile                             # Dockerfile for containerizing the project
        ├── 📄 requirements.txt                       # List of dependencies
```

## ⚙️ Prerequisites

- Python 3.11.7
- Git
- Docker (for containerization)
- GCP Components(Bigquery, CloudBuild, CloudRun, Vertex AI)
- GoogleCloud SDK

## 🔧 Installation

To set up the project on your local machine, follow these steps:

**1. Clone the Repository**

```bash
git clone project_name
cd project_name
```

**2. Set Up Docker**

To containerize the project, you can build and run the Docker image:

```bash
# Authenticate Docker to your ECR
gcloud auth application-default login

# Build docker image
docker build -t docker-image-name .
```

**3. Push to GCP Artifacts Registry**

Push the Docker image to your GCP Artifacts Registry:

```bash
# Push the Docker image to ECR
gcloud builds submit --tag gcr.io/<your-project-id>/<docker-image-name> --timeout=2h
```

**4. Create Cloud Run Service**

Using the image from the GCP Artifacts registry created above, create a cloud run service:

1. Go to the cloud run console and click on "Create service."
2. Choose "Container image" and enter port number.
3. Configure your function's settings, such as memory and timeout.
4. Deploy the function.

After deploying the function, it will display the URL link as below.

Below is the URL to access the application: 

https://marketing-analytics-bot-xxxxx-uc.a.run.app

## 🚀 CI/CD Setup Using Google Cloud Build

The CI/CD pipeline is configured in a `cloudbuild.yml` file, which defines the steps to be executed whenever new code is pushed to the main branch.

Steps in cloudbuild.yml:

The cloudbuild.yml file contains the following key steps:

**1. Build the Docker Image**

The Docker image for the application is built using the code in the repository. The image is tagged with the commit SHA to ensure version control.

**2. Push the Image to Google Cloud Artifact Registry**

Once the Docker image is built, it is pushed to the Google Cloud Artifact Registry. This centralizes the image storage and makes it easily accessible for deployment.

**3. Deploy to Google Cloud Run**

The Docker image is deployed to an existing Google Cloud Run service. The deployment is configured to use the newly built image, ensuring that the latest version of the application is running.
---