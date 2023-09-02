""" BlazeLink monitoring API """

from fastapi import APIRouter

router = APIRouter()


@router.get("/subscriptions")
def get_subscriptions():
    from main import subs

    data = {}

    for conn_id in subs._subscriptions:

        conn_subs = []

        for sub in subs._subscriptions[conn_id]:
            conn_subs.append(
                {
                    "id": sub.obj_id,
                    "entity": sub.entity,
                    "dependencies": [
                        {
                            "id": dep.obj_id,
                            "entity": dep.entity,
                            "dependencies_should_be_0": len(dep._dependencies)
                        } for dep in sub.collect_dependencies()
                    ],
                    "ref_count": sub._registry[hash(sub)][1]
                }
            )

        data[conn_id] = conn_subs

    return {
        'subscriptions': data
    }
