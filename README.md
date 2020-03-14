# gavel-apiserver
API Server for Gavel Project

## Usage
```shell
./manage.py makemigrations
./manage.py migrate
./manage.py runserver
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