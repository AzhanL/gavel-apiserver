import graphene
import graphql_jwt

import apiserver.schema


class Query(apiserver.schema.Query, graphene.ObjectType):
    pass


class Mutation(apiserver.schema.Mutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
