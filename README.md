# py_jama_client

A python Jama Connect REST API client library

## Acknowledgments

This client library is heavily inspired by, and even based on the client library created by the Jama team [py-jama-rest-client](https://github.com/jamasoftware-ps/py-jama-rest-client). However, due to inactivity I have taken it upon myself to create a distinct package for those who have a need for a more comprehensive client -- specifically for the use of embedded resources.

## Jama Software

Jama Software is the definitive system of record and action for product development. The company’s modern requirements and test management solution helps enterprises accelerate development time, mitigate risk, slash complexity and verify regulatory compliance. More than 600 product-centric organizations, including NASA, Boeing and Caterpillar use Jama to modernize their process for bringing complex products to market. The venture-backed company is headquartered in Portland, Oregon. For more information, visit jamasoftware.com.

Please visit dev.jamasoftware.com for additional resources and join the discussion in our community community.jamasoftware.com.

### Requirements

* [Python 3.11 or greater](https://www.python.org/downloads/release/python-372/)

### Installation

```bash
pip install py-jama-client
```

### Usage

#### Basic

```python
from py_jama_client.client import JamaClient # import client
from py_jama_client.apis.abstract_items_api import AbstractItemsAPI # import API

client = JamaClient(
    host="example.jamacloud.com", 
    credentials=("my_username", "my_password"),
) # create client instance

abstract_items_api = AbstractItemsAPI(client) # pass client instance to API

abstract_items = abstract_items_api.get_abstract_items() # use API methods to fetch resources

print(abstract_items.data)
```

#### With Links

```python
from py_jama_client.client import JamaClient # import client
from py_jama_client.apis.items_api import ItemsAPI # import API

client = JamaClient(
    host="example.jamacloud.com", 
    credentials=("my_username", "my_password"),
) # create client instance

items_api = ItemsAPI(client) # pass client instance to API

items = items_api.get_items(
    project_id=82, 
    params={'include': ('data.itemType', 'data.childItemType', )}, 
    # NOTE: 'params' must be a key-word argument
) # use API methods to fetch resources, include itemTypes, and childItemTypes in response

print(items.data, items.linked)
```

### Additional Notes

Please be aware that this package is a work-in-progress, and some API methods may be missing from the source code. Please open an issue, or submit a pull-request (see CONTRIBUTING.md for more).
