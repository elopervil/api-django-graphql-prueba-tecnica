# API (Django-GraphQL-Postgresql)

This API provides us:
* User creation and modification
* User Authentication
* Creation, modification, and deletion of ideas
* Follow-up request between users

And uses the following core packages:
* [django](https://pypi.org/project/Django/)
* [graphene-django](https://pypi.org/project/graphene-django/)
* [django-graphql-jwt](https://pypi.org/project/django-graphql-jwt/)
* [psycopg2](https://pypi.org/project/psycopg2/)

## Requirements

* **Docker**
* **Docker-compose**
* **Postman**

## Installation

1. **Clone repository**

```bash
$ git clone https://github.com/elopervil/api-django-graphql-prueba-tecnica
```

2. **Run docker-compose command**

In the root directory of the project we run the command:

```bash
$ docker-compose up
```

## Usage

To utilize this API, we will use the Postman client. After installation, the URL for the graphql endpoint will be available at http://localhost:8000/graphql/. 
In a new workspace within the Postman client, enter the URL, set the method to POST, and select GraphQL in the body content to ensure proper formatting of requests

* #### Query User:

1. **users**

The response to this request is a list of registered users. For example:

```
query{
    users{
        username
        email
    }
}
```

2. **me**

The response to this request includes all data of the authenticated user, such as personal information, a list of followed users, a list of followers, a list of published ideas, and a list of received and sent follow-up requests. 
To access this request, the user must be authenticated (this will be explained in more detail later). For example:

```
query{
    me{
        email
        username
        following{
            username
        }
        followers{
            username
        }
        ideaUser{
            content
            visibility
        }
        followRecived{
            requester{
                username
            }
        }
        followSend{
            toFollow{
                username
            }
        }
    }
}
```

3. **searchUsers**

The response to this request is a list of users that contain the string passed as a parameter in their usernames. Authentication is required for this request. For example:

```
query{
    searchUsers(username:"stringExample"){
        username
        email
    }
}
```

4. **forgottenPassword**

This request will be used to recover the user's password. The backend will send an email to the user with a magic link for this purpose (using an email template). 
This is implemented using Django's core.mail.backends.EmailBackend (the email will be printed in the console). To send real emails, change this setting to the Django SMTP backend. For example:

```
query{
    forgottenPassword(email:"user@example.com")
}
```

* #### Mutation User

1. **register**

The response to this request is the creation of a new user. To do this, we must include the email, username, and password in the request. 
The response will also provide us with the token for authentication. For example:

```
mutation{
    register(email:"example@example.com", username:"exampleUser", password:"example1234"){
        user{
            email
            username
        }
        token
    }
}
```

2. **tokenAuth**

This mutation is for logging in. The response to this request is the user's token. To do this, we must include the user's email and password. For example:

```
mutation{
    tokenAuth(email: "userMail@example.com", password:"example1234"){
        token
        payload
    }
}
```
This token will be used in the request header. We pass it to the "Authorization" key.

3. **changePassword**

The response to this request is a change of password for the authenticated user. We must include the new password in the request. For example:

```
mutation{
    changePassword(password:"newPassword"){
        success
        error
    }
}
```

4. **unfollow**

The response to this request is to remove a user from the authenticated user's followed list. We must include the user's ID in the request. For example:

```
mutation{
    unfollow(idUser: 1){
        success
        message
        error
    }
}
```

5. **removeFollower**

The response to this request is to remove a follower from the authenticated user's follower list. We must include the user's ID in the request. For example:

```
mutation{
    removeFollower(idUser: 1){
        success
        message
        error
    }
}
```

* #### Query Idea

1. **listAllIdeas**

The response to this request is a list of users' ideas ordered by publication date. 
To access this, we must be authenticated. If we are following the user, we can view their ideas with visibility of PUBLIC or PROTECTED. 
If we are not following the user, we can only view their PUBLIC ideas. We can view all of our ideas (PUBLIC, PROTECTED, and PRIVATE).

```
query{
    listAllIdeas{
        content
        visibility
        pubUser{
            username
        }
    }
}
```

2. **listMyIdeas**

The response to this request is a list of all ideas of the authenticated user (PUBLIC, PROTECTED, and PRIVATE). 
To access this, we must be authenticated. For example:

```
query{
    listMyIdeas{
        content
        visibility
        pubDate
    }
}
```

3. **listFollowedIdeas**

The response to this request is a list of ideas from the following user (only PUBLIC and PROTECTED) that can be viewed only by authenticated users. 
We must include the following user's ID in the request. For example:

```
query{
   listFollowedIdeas(idUser: 1){
       content
       visibility
       pubDate
   }
}
```

* #### Mutation Idea

1. **addIdea**

The response to this request is the creation of a new idea for the authenticated user. 
We must include the content text of the idea. If we do not specify the visibility argument, it will default to public. For example:

```
mutation{
    addIdea(content:"text idea example", visibility:"private"){
        success
        error
        idea{
            content
            visibility
            pubDate
        }
    }
}
```

2. **editIdea**

The response to this request is the modification of a user's idea (content, visibility, or both). 
The only required argument is the idea's ID. To access this, we must be authenticated. For example:

```
mutation{
    editIdea(id: 1, content:"text example", visibility:"protected"){
        success
        error
        idea{
            content
            visibility
            pubDate
        }
    }
}
```

3. **deleteIdea**

The response to this request is the removal of an idea belonging to the authenticated user. 
We must include the idea's ID in the request. For example:

```
mutation{
    deleteIdea(id:1){
        success
        error
        message
    }
}
```

* #### Query Follow Request

1. **followUpRequest**

The response to this request is a list of received follow-up requests. To access this, we must be authenticated. For example:

```
query{
    followUpRequest{
        requester{
            username
        }
        status
    }
}
```

* #### Mutation Follow Request

1. **sendFollowRequest**

The response to this request is to send a follow-up request to the selected user. 
To access this, we must be authenticated. The only argument required is the user we want to follow.

```
mutation{
    sendFollowRequest(idUser:1){
        success
        error
        message
        followRequest{
            toFollow{
                username
            }
            status
        }
    }
}
```

2. **responseFollowRequest**

The response to this request is to accept or deny a follow request. We must include the following request's ID and the response (True or False) in the request. 
To access this, we must be authenticated. For example:

```
mutation{
    responseFollowRequest(idRequest: 1, response: true){
        success
        error
        message
        followRequest{
            requester{
                username
            }
            status
        }
    }
}
```

## Notifications

* ### To implement Push Notifications

we can use the package **fcm-django** which works with Firebase Cloud Messaging. 
It serves as a unified platform for sending push notifications to mobile devices and browsers. 
This package provides us with a model for registering devices (FCMDevice). 
I suggest that we register the device when a user registers. 
Later, when a user adds an idea, we can include the option to send a push notification to their followers in the "addIdea" mutation. 
[You can view the documentation for this package here](https://github.com/xtrinch/fcm-django)
