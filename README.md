# UFO Dashboard

This project is a UFO sightings dashboard that provides visualizations and analysis of UFO sightings data. It also fetches and displays weather data for the time and location of each sighting.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

What things you need to install the software and how to install them:

- Python 3.x
- pandas
- requests
- SQLAlchemy
- dash

### Installing and Usage

A step by step series of examples that tell you how to get a development environment running:

1. Clone the repository
2. Install the dependencies using pip:

```bash
pip install -r requirements.txt
```

3. Start database server:

```bash
docker-compose up -d
```

4. Run the script to upload database dump:

```bash
pg_restore -d db_name /path/to/your/file/dump_name.sql -c -U db_user
```

5. Change HOST in main.py to your local network IP address:

```python
HOST = 'your_local_ip_address'
```

6. Run the main application:

```bash
python main.py
```