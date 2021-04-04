__author__ = "Eetu Asikainen"

from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
from xml.etree import ElementTree
import threading
import datetime
import sys
import wikipedia
from typing import Optional


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = "/ass2"


def parser_helper(element: ElementTree.Element) -> Optional[str]:
    notes = element.findall('note')
    str_construct = ""
    for index, note in enumerate(notes, 1):
        str_construct += f"Note {index}: "\
            f"{note.attrib['name']}\n" + \
            f"{note.find('text').text.lstrip().rstrip()}\n" + \
            f"Added {note.find('timestamp').text.lstrip().rstrip()}\n"

    return str_construct or None


class XMLReader:
    def __init__(self, file_name: str = 'db'):
        self._file = f'{file_name}.xml'
        self._file_lock = threading.Lock()

    def find(self, topic: str) -> Optional[str]:
        with self._file_lock:
            element_tree = ElementTree.parse(self._file)
            data_elements = element_tree.getroot().findall('topic')
            for data_element in data_elements:
                if data_element.attrib['name'] == topic:
                    return parser_helper(data_element)

    def add(self, topic: str, fact_name: str, fact_text: str) -> str:
        with self._file_lock:
            element_tree = ElementTree.parse(self._file)
            data_elements = element_tree.getroot().findall('topic')

            for child in data_elements:
                if child.attrib['name'] == topic:
                    data_element = child
                    break
            else:
                data_element = ElementTree.SubElement(element_tree.getroot(), 'topic', {'name': topic})

            for child in data_element.findall('note'):
                if child.attrib['name'] == fact_name:
                    note_element = child
                    break
            else:
                note_element = ElementTree.SubElement(data_element, 'note', {'name': fact_name})

            text_element = ElementTree.SubElement(note_element, 'text')
            text_element.text = fact_text

            datetime_element = ElementTree.SubElement(note_element, 'timestamp')
            datetime_element.text = datetime.datetime.now().strftime("%m/%d/%y - %H:%M:%S")

            element_tree.write(self._file)

        return "Successfully added data to the xml."


def server_loop(file_name: str = 'db', host: str = 'localhost', port: int = 8000):
    reader = XMLReader(file_name)
    with SimpleXMLRPCServer((host, port), requestHandler=RequestHandler) as server:
        server.register_introspection_functions()

        @server.register_function
        def read_data(topic: str) -> Optional[str]:
            return reader.find(topic)

        @server.register_function
        def write_data(topic: str, note_name: str, note: str) -> str:
            return reader.add(topic, note_name, note)

        @server.register_function
        def query_wikipedia(topic: str) -> list:
            result = wikipedia.search(topic)
            for page in result:
                try:
                    wikipedia.summary(page)
                except wikipedia.DisambiguationError:
                    result.remove(page)

            return result

        @server.register_function
        def add_wiki_result(topic: str, page_name: str) -> (str, str, str):
            data = wikipedia.summary(page_name)
            return reader.add(topic, f"Wikipedia summary: {page_name}", data)

        print(f"Now serving on f{host}:{port}/ass2")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer interrupted with keyboard interrupt. Shutting down.")
            sys.exit(0)


if __name__ == "__main__":
    server_loop()
