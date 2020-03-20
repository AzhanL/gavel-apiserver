# gavel-apiserver
API Server for Gavel Project


## Requirements
For apt (Ubuntu, Debian...):
```bash
sudo apt-get install python3-dev  
```

For yum (CentOS, RHEL...):
```bash
sudo yum install python3-devel   # for python3.x installs
```

For dnf (Fedora...):
```bash
sudo dnf install python3-devel  # for python3.x installs
```

## Full Command Deploy
```shell
pip3 install pipenv
pipenv --python 3.7
pipenv shell
pipenv install
./manage.py makemigrations
./manage.py migrate
./manage.py collectstatic

pip3 install uwsgi
uwsgi uwsgi.ini
```

#### Update Court Info
```json
mutation {
  updateCourtInfo {
    successful
    statusMessage
  }
}
```
#### Query Court Info
```json
query{
  courts {
    name
    courtBranch
    courtType
    courtSpecialization
    locations {
      name
      addressLine1
      operationalDays {
        weekDay
        timeSlots {
          openTime
          closeTime
        }
      }
      roomSet {
        roomNumber
      }
    }
  }
}

```