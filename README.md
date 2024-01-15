# iLens API

This is the backend API for the iLens project.

## Setting Up The Project
> You need a linux machine to run this project.

### 1. Install Python 3.10

### 2. Install Poetry
```bash
pip install poetry
```

### 3. Create Virtual Environment & Install Dependencies
```bash
make install
```

### 4. Activate Virtual Environment
```bash
source ./activate
```
> This also exports all variables in the .env file to the environment.

### 5. Run The Project
```bash
# Run the development server
make dev

# Run the production server
make run
```