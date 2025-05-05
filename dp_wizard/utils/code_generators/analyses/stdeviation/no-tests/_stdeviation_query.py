groups = GROUP_NAMES
QUERY_NAME = (
    context.query().group_by(groups).agg(EXPR_NAME)
    if groups
    else context.query().select(EXPR_NAME)
)

print(QUERY_NAME)  # A LazyFrameQuery
STATS_NAME = QUERY_NAME.release().collect()
# print(STATS_NAME)
