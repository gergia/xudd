import base64
import uuid

from xudd import PY2


def base64_uuid4():
    """
    Return a base64 encoded uuid4
    """
    base64_encoded = base64.urlsafe_b64encode(uuid.uuid4().bytes)
    if not PY2:
        base64_encoded = base64_encoded.decode("utf-8")

    return base64_encoded.rstrip("=")


def is_qualified_id(actor_id):
    """
    See whether or not this actor id is fully qualified (has the
    @hive-id attached) or not.
    """
    return u"@" in actor_id


def split_id(actor_id):
    """
    Split an actor id into ("actor-id", "hive-id")

    If no hive-id, it will be None.
    """
    components = actor_id.split(u"@", 1)
    if len(components) == 1:
        components.append(None)

    return components


def possibly_qualify_id(actor_id, hive_id):
    """If this actor doesn't already have a hive id assigned to it, assign it

    Note that you can specify a hive_id here, and if there is already
    a hive_id on the actor_id, it simply won't assign something.  This
    is useful if you want to declare an actor as local if it's not
    assigned, but let it stay remote if it is.
    """
    # it's already qualified, just return it
    if is_qualified_id(actor_id):
        return actor_id

    return u"%s@%s" % (actor_id, hive_id)
