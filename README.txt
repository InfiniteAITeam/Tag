This project is Infinte python based ai dependent code tagging project


base-docker/v1 - the root for base docker images
base-docker/v1/taggerxvfb - the root for Docker image for ait/taggerxvfb

backend/v1/src - the root for all python source code
frontend/v1/src - the root for web front end

docker-compose-app.yml - the docker compose file to stand up the web frontend
docker-compose-taggerx.yml - the docker compose file to run the tagger

prunner.sh - utility shel script that can be used to build base images and then
    stand up up or tagger



Graph Diagram

    "Step 1: TechSpec Generation"
        A[Start] --> B{User provides Figma URL and Acceptance Criteria};
        B --> C[Clicks "Generate TechSpec"];
        C --> D{API Call: POST /generate-techspec};
        D --> E{API returns TechSpec data};
        E --> F[UI displays TechSpec and Figma previews];
        F --> G[User clicks "Next"];
    end

    subgraph "Step 2: Suggest Tagging"
        G --> H{User provides GitHub Repo URL};
        H --> I[Clicks "Suggest Tagging"];
        I --> J{API Call: POST /suggest-tagging};
        J --> K{API returns Implementation Guide};
        K --> L[UI displays Markdown preview of the guide];
        L --> M[User clicks "Next"];
    end

    subgraph "Step 3: Apply Tagging"
        M --> N[User is on the Apply Tagging screen];
        N --> O[Clicks "Apply Tagging"];
        O --> P{API Call: POST /apply-tagging};
        P --> Q{API applies changes to the repo};
        Q --> R[UI updates to show "Results" section];
    end
