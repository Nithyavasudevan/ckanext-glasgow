import datetime

import sqlalchemy

import ckan


harvest_last_audit_table = sqlalchemy.Table(
    'harvest_last_audit', ckan.model.meta.metadata,
    sqlalchemy.Column('audit_id',
                      sqlalchemy.types.UnicodeText,
                      primary_key=True),
    sqlalchemy.Column('harvest_job_id',
                      sqlalchemy.types.UnicodeText),
    sqlalchemy.Column('created',
                      sqlalchemy.types.DateTime,
                      default=datetime.datetime.utcnow),
    )


class HarvestLastAudit(ckan.model.DomainObject):
    def __init__(self, audit_id, harvest_job_id, created=None):
        self.audit_id = audit_id
        self.harvest_job_id = harvest_job_id
        self.created = created


ckan.model.meta.mapper(HarvestLastAudit,
                       harvest_last_audit_table)


def setup():
    if not harvest_last_audit_table.exists():
        harvest_last_audit_table.create()
