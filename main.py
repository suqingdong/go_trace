import re
import sys
import json

import click


def parse_obo_term(infile):
    with open(infile) as f:
        term = {}
        for line in f:
            if line.startswith('[Term]'):
                if term:
                    yield term
                term = {}
                continue

            if line.startswith('id:'):
                term_id = line.strip().split(':', 1)[1].strip()
                term[term_id] = {'parents': []}
            elif line.startswith('is_a:') or line.startswith('relationship:'):
                parent_id = re.findall(r'GO:\d+', line)[0]
                term[term_id]['parents'].append(parent_id)
            elif line.startswith('is_obsolete:'):
                term[term_id]['parents'] = ['is_obsolete']
            elif line.startswith('name:'):
                term[term_id]['name'] = line.strip().split(':', 1)[1].strip()
            elif line.startswith('namespace:'):
                term[term_id]['namespace'] = line.strip().split(':', 1)[1].strip()
            elif line.startswith('[Typedef]'):
                yield term
                break


def trace_ancestor_paths(term_id, all_terms):
    """
    Trace all ancestor paths for a given term.

    :param term_id: The term ID whose ancestor paths are to be found.
    :param all_terms: A dictionary of all terms with their parents.
    :return: A list of lists, where each inner list is a path from the term to one of its farthest ancestors.
    """
    paths = []
    def recurse(current_term, current_path):
        if current_term not in all_terms or not all_terms[current_term]['parents']:
            paths.append(current_path)
            return
        for parent_id in all_terms[current_term]['parents']:
            recurse(parent_id, current_path + [parent_id])

    recurse(term_id, [term_id])
    return paths


@click.command(
    no_args_is_help=True,
)
@click.option('-i', '--go-obo-file', help='the GO obo file', default='go-basic.obo', show_default=True, type=click.Path(exists=True))
@click.option('-o', '--outfile', help='the output filename [stdout]')
@click.option('-t', '--term', help='a specific GO term to trace')
def main(go_obo_file, outfile, term):

    out = open(outfile, 'w') if outfile else sys.stdout

    all_terms = {}
    with open('all_go_terms.xls', 'w') as temp:
        title = '#GoId Name NameSpace Parents'.split()
        temp.write('\t'.join(title) + '\n')
        for go_term in parse_obo_term(go_obo_file):
            all_terms.update(go_term)
            go_id = list(go_term.keys())[0]
            linelist = [go_id, go_term[go_id]['name'], go_term[go_id]['namespace'], ','.join(go_term[go_id]['parents'])]
            temp.write('\t'.join(linelist) + '\n')

    term_id_list = [term] if term else all_terms

    with out:
        for term_id in term_id_list:
            if all_terms.get(term_id) and all_terms[term_id].get('parents') == ['is_obsolete']:
                linelist = [term_id, 'is_obsolete']
                out.write('\t'.join(linelist) + '\n')
            else:
                ancestor_paths = trace_ancestor_paths(term_id, all_terms)
                for path in ancestor_paths:
                    linelist = [term_id] + path[1:][::-1]
                    out.write('\t'.join(linelist) + '\n')


if __name__ == '__main__':
    main()
