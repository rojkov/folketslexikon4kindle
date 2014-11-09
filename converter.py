#!/usr/bin/env python3

import xml.parsers.expat
from jinja2 import Template
import argparse

classes = {
    "vb":     "v.",
    "nn":     "n.",
    "ab":     "adv.",
    "jj":     "adj.",
    "abbrev": "abbr.",
    "pn":     "pn",
    "ie":     "i.",
    "in":     "i.",
    "rg":     "cardinal",
    "pm":     "name",
    "kn":     "conj.",
    "pp":     "pp."
}

prolog = """<html xmlns:math="http://exslt.org/math" xmlns:svg="http://www.w3.org/2000/svg"
xmlns:tl="http://www.kreutzfeldt.de/tl"
xmlns:saxon="http://saxon.sf.net/" xmlns:xs="http://www.w3.org/2001/XMLSchema"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:cx="http://www.kreutzfeldt.de/mmc/cx"
xmlns:dc="http://purl.org/dc/elements/1.1/"
xmlns:mbp="http://www.kreutzfeldt.de/mmc/mbp"
xmlns:mmc="http://www.kreutzfeldt.de/mmc/mmc"
xmlns:idx="http://www.mobipocket.com/idx">
<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /></head>
<body>
<mbp:frameset>
"""

epilog = """
</mbp:frameset>
</body>
</html>
"""

tplstr = """
<idx:entry name="swedish" scriptable="yes" spell="yes">
<a id="{{anchor}}"></a>
<idx:short>
    <idx:orth value="{{ word.value|replace('|','') }}">{{ word.value }}
    {% if word.class and classes[word.class] %}<i>{{ classes[word.class] }}</i>{% elif word.class %}<i>{{ word.class}}</i>{% endif %}
        {% if inflections or derivations or compounds %}
        <idx:infl>
        {% for inflection in inflections %}
            <idx:iform value="{{ inflection|replace('|','') }}" exact="yes" />
        {% endfor %}
        {% for deriv in derivations %}
            <idx:iform value="{{deriv.value|replace('|','')}}" exact="yes" />
            {% if deriv.inflection %}<idx:iform value="{{deriv.inflection|replace('|','')}}" exact="yes" />{% endif %}
        {% endfor %}
        {% for compound in compounds %}
            <idx:iform value="{{compound.value|replace('|','')}}" exact="yes" />
            {% if compound.inflection %}<idx:iform value="{{compound.inflection|replace('|','')}}" exact="yes" />{% endif %}
        {% endfor %}
        </idx:infl>
        {% endif %}
    </idx:orth>
    <p>{% for translation in translations %}<b>{{ translation.value }}</b>{% if translation.comment %} ({{ translation.comment }}){% endif %}{% if not loop.last %}, {% endif %}{% endfor %}</p>
    {% if inflections %}
    <p><i>Inflections:</i> {% for infl in inflections %}{{ infl }}{% if not loop.last%}, {% endif %}{% endfor %}</p>
    {% endif %}
    {% if synonyms %}
    <p><i>Synonyms:</i> {% for syn in synonyms %}{{ syn }}{% if not loop.last%}, {% endif %}{% endfor %}</p>
    {% endif %}
    {% for definition in definitions %}
    <p><i>Definition:</i> {{definition.value}}{% if definition.translation %} [{{ definition.translation }}]{% endif %}</p>
    {% endfor %}
    {% if idioms %}
    <p><i>Idioms:</i><ul>
    {% for idiom in idioms %}
        <li>{{ idiom.value }}{% if idiom.translation %} [{{ idiom.translation }}]{% endif %}</li>
    {% endfor %}
    </ul></p>
    {% endif %}
    {% if examples %}
    <p><i>Examples:</i><ul>
    {% for example in examples %}
        <li>{{ example.value }}{% if example.translation %} [{{ example.translation }}]{% endif %}</li>
    {% endfor %}
    </ul></p>
    {% endif %}
    {% if derivations %}
    <p><i>Derivations:</i><ul>
    {% for deriv in derivations %}
        <li>{{ deriv.value }}{%if deriv.inflection %}, {{ deriv.inflection }}{% endif %}{% if deriv.translation %} [{{ deriv.translation }}]{% endif %}</li>
    {% endfor %}
    </ul></p>
    {% endif %}
    {% if compounds %}
    <p><i>Compound forms:</i><ul>
    {% for compound in compounds %}
        <li>{{ compound.value }}{%if compound.inflection %}, {{ compound.inflection }}{% endif %}{% if compound.translation %} [{{ compound.translation }}]{% endif %}</li>
    {% endfor %}
    </ul></p>
    {% endif %}
</idx:short>
</idx:entry>
"""

class Entry:

    states = ("empty", "word", "example", "derivation", "compound", "paradigm",
              "definition", "idiom")
    transitions = {
        "empty": ("word",),
        "word": ("example", "derivation", "compound", "paradigm", "empty",
                 "definition", "idiom"),
        "example": ("word",),
        "derivation": ("word",),
        "compound": ("word",),
        "paradigm": ("word",),
        "definition": ("word",),
        "idiom": ("word",)
    }
    tpl = Template(tplstr)

    def __init__(self, file_handle):
        self.state = "empty"
        self.file_handle = file_handle
        self.anchor_id = 0
        self.cleanup()

    def cleanup(self):
        self.word = None
        self.translations = []
        self.unknown_depth = 0
        self.inflections = []
        self.synonyms = []
        self.defs = []
        self.idioms = []
        self.examples = []
        self.derivations = []
        self.compounds = []

    def set_state(self, new_state):
        if new_state in self.transitions[self.state]:
            self.state = new_state
        else:
            str = "wrong transition %s => %s" % (self.state, new_state)
            print(str)
            exit(0)

    def start_element(self, name, attrs):
        if self.unknown_depth > 0:
            self.unknown_depth = self.unknown_depth + 1
            return

        if name == "word":
            self.add_word(attrs)
        elif name == "translation":
            self.add_translation(attrs)
        elif name == "paradigm":
            self.set_state("paradigm")
        elif name == "inflection":
            self.add_inflection(attrs)
        elif name == "synonym":
            self.add_synonym(attrs)
        elif name == "definition":
            self.add_definition(attrs)
        elif name == "idiom":
            self.add_idiom(attrs)
        elif name == "example":
            self.add_example(attrs)
        elif name == "derivation":
            self.add_derivation(attrs)
        elif name == "compound":
            self.add_compound(attrs)
        elif self.state != "empty":
            self.unknown_depth = 1

    def add_word(self, attrs):
        self.set_state("word")
        self.word = attrs

    def add_translation(self, attrs):
        if self.state == "word":
            self.translations.append(attrs)
        elif self.state == "definition":
            self.defs[-1]["translation"] = attrs["value"]
        elif self.state == "idiom":
            self.idioms[-1]["translation"] = attrs["value"]
        elif self.state == "example":
            self.examples[-1]["translation"] = attrs["value"]
        elif self.state == "derivation":
            self.derivations[-1]["translation"] = attrs["value"]
        elif self.state == "compound":
            self.compounds[-1]["translation"] = attrs["value"]

    def add_inflection(self, attrs):
        if self.state == "paradigm":
            self.inflections.append(attrs["value"])

    def add_synonym(self, attrs):
        if self.state == "word":
            self.synonyms.append(attrs)

    def add_definition(self, attrs):
        self.set_state("definition")
        self.defs.append(attrs)

    def add_idiom(self, attrs):
        self.set_state("idiom")
        self.idioms.append(attrs)

    def add_example(self, attrs):
        self.set_state("example")
        self.examples.append(attrs)

    def add_derivation(self, attrs):
        self.set_state("derivation")
        self.derivations.append(attrs)

    def add_compound(self, attrs):
        self.set_state("compound")
        self.compounds.append(attrs)

    def end_element(self, name):
        if self.unknown_depth > 0:
            self.unknown_depth = self.unknown_depth - 1
            return

        if name == "word":
            self.set_state("empty")

            def synkey(syn):
                if "level" in syn:
                    return float(syn["level"])
                else:
                    return 5.0

            self.synonyms.sort(key=synkey, reverse=True)
            self.anchor_id = self.anchor_id + 1

            output = self.tpl.render({
                "word": self.word,
                "translations": self.translations,
                "inflections": self.inflections,
                "synonyms": [syn["value"] for syn in self.synonyms],
                "definitions": self.defs,
                "idioms": self.idioms,
                "derivations": self.derivations,
                "compounds": self.compounds,
                "examples": self.examples,
                "classes": classes,
                "anchor": self.anchor_id
            })
            self.file_handle.write(output)
            self.cleanup()
        elif name == "paradigm":
            self.set_state("word")
        elif name == "definition":
            self.set_state("word")
        elif name == "idiom":
            self.set_state("word")
        elif name == "example":
            self.set_state("word")
        elif name == "derivation":
            self.set_state("word")
        elif name == "compound":
            self.set_state("word")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="original Folkets Lexikon XML file")
    parser.add_argument("dest", help="output file")
    args = parser.parse_args()

    with open(args.dest, "w") as out:
        with open(args.source, "rb") as f:
            p = xml.parsers.expat.ParserCreate()

            out.write(prolog)
            el = Entry(out)
            p.StartElementHandler = el.start_element
            p.EndElementHandler = el.end_element
            p.ParseFile(f)
            out.write(epilog)

if __name__ == "__main__":
    main()
