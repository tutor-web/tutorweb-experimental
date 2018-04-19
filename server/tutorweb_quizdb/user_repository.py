from pluserable.data.sqlalchemy.repository import Repository as PluserableRepository


class Repository(PluserableRepository):
    """
    Override methods in pluserable's repo to support hostDomain
    """
    def q_user_by_id(self, id):
        """Return a user with ``id``, or None."""
        return self.sas.query(self.User).get((self.User.active_host_domain(), id,))
