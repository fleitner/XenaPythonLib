import csv

def _find_total_leaf_nodes(stats):
    leaf = 0
    if type(stats) is dict:
        for k in stats.keys():
            leaf += _find_total_leaf_nodes(stats[k])
    else:
        return 1

    return leaf

def _find_total_nr_stats(stats):
    first_sample_key = stats.keys()[0]
    return _find_total_leaf_nodes(stats[first_sample_key])

def _insert_centered_field(value, nr_leafs):
    line = [''] * nr_leafs
    line[nr_leafs / 2] = value
    return line

def _build_unit_header_line(stats):
    header = ['timestamp']
    # first sample only
    first_sample_key =  stats.keys()[0]
    testnames = stats[first_sample_key].keys()
    for test in testnames:
        if type(stats[first_sample_key][test]) is dict:
            testunits = stats[first_sample_key][test].keys()
            if len(testunits):
                header += testunits
                continue
        testunits = [ 'ND' ]
        header += testunits
    return header

def _build_values_lines(stats):
    values = []
    sample_list = stats.keys()
    sample_list.sort()
    for sample in sample_list:
        sample_values = [ sample ]
        testnames = stats[sample].keys()
        for test in testnames:
            if type(stats[sample][test]) is dict:
                testunits = stats[sample][test].keys()
                for unit in testunits:
                    sample_values.append(stats[sample][test][unit])
                continue
            sample_values.append('ND')
        values.append(sample_values)
    return values

def _build_test_header_line(stats, nr_columns):
    header = ['timestamp']
    # first sample only
    first_sample_key =  stats.keys()[0]
    testnames = stats[first_sample_key].keys()
    for test in testnames:
        nr_childs = _find_total_leaf_nodes(stats[first_sample_key][test])
        header += _insert_centered_field(test, nr_childs)

    return header


def write_csv(filename, title, stats):
    csv_file = open(filename, 'w+b')
    csvwriter = csv.writer(csv_file)
    nr_columns = _find_total_nr_stats(stats)
    title_line = _insert_centered_field(title, nr_columns)
    csvwriter.writerow(title_line)
    tests_line = _build_test_header_line(stats, nr_columns)
    csvwriter.writerow(tests_line)
    units_list = _build_unit_header_line(stats)
    csvwriter.writerow(units_list)
    values_list = _build_values_lines(stats)
    csvwriter.writerows(values_list)
    csv_file.close()

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
