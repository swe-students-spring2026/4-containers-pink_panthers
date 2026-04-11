"""
Test file to verify ML container is running correctly.
And to verify that the database connection is working correctly.
"""

from db import insert_result

sample_result = {
    "colors": ["blue", "white"],
    "result": "match",
}

insert_result(sample_result)

print("Inserted test result!")
