import pymongo.results


def bulk_write_result_rich_repr(self):
    yield "acknowledged", self.acknowledged
    yield "bulk_api_result", self.bulk_api_result
    yield "deleted_count", self.deleted_count
    yield "inserted_count", self.inserted_count
    yield "matched_count", self.matched_count
    yield "modified_count", self.modified_count
    yield "upserted_count", self.upserted_count
    yield "upserted_ids", self.upserted_ids


def delete_result_rich_repr(self):
    yield "deleted_count", self.deleted_count
    yield "acknowledged", self.acknowledged


def insert_many_result_rich_repr(self):
    yield "acknowledged", self.acknowledged
    yield "inserted_ids", self.inserted_ids


def insert_one_result_rich_repr(self):
    yield "acknowledged", self.acknowledged
    yield "inserted_id", self.inserted_id


def update_result_rich_repr(self):
    yield "acknowledged", self.acknowledged
    yield "matched_count", self.matched_count
    yield "modified_count", self.modified_count
    yield "upserted_id", self.upserted_id


def apply():
    pymongo.results.BulkWriteResult.__rich_repr__ = bulk_write_result_rich_repr
    pymongo.results.DeleteResult.__rich_repr__ = delete_result_rich_repr
    pymongo.results.InsertManyResult.__rich_repr__ = insert_many_result_rich_repr
    pymongo.results.InsertOneResult.__rich_repr__ = insert_one_result_rich_repr
    pymongo.results.UpdateResult.__rich_repr__ = update_result_rich_repr
