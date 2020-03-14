import graphene

import apiserver.schema


class Query(apiserver.schema.Query, graphene.ObjectType):
    pass


class Mutation(apiserver.schema.Mutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
