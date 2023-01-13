import graphene
import graphql_jwt
from .types import UserQuery, UserMutation, IdeaQuery, IdeaMutation, FollowRequestQuery, FollowRequestMutation


class Query(UserQuery, IdeaQuery, FollowRequestQuery, graphene.ObjectType):
    pass


class Mutation(UserMutation, IdeaMutation, FollowRequestMutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)