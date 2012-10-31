#!/usr/bin/env python
import yaml
import markdown
import os
import argparse
import copy
from Cheetah.Template import Template
import shutil


class mdw_value():
    def __init__(self, origin, value):
        self.origin = origin
        self.value = value

    def __str__(self):
        return self.value


class writeable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        target_dir = os.path.abspath(values)
        prospective_dir = target_dir
        if not os.path.isdir(prospective_dir):
            prospective_dir = os.path.dirname(prospective_dir)
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
               "writeable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, target_dir)
        else:
            raise argparse.ArgumentTypeError(
                "writeable_dir:{0} is not a writeable dir".format(
                    prospective_dir))


class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir = os.path.abspath(values)
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError(
                "readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace, self.dest, prospective_dir)
        else:
            raise argparse.ArgumentTypeError(
                "readable_dir:{0} is not a readable dir".format(
                    prospective_dir))


def read_dir_config(directory, parent_config):
    new_config = copy.deepcopy(parent_config)
    config_file = os.path.join(directory, 'mdw')
    if os.path.isfile(config_file):
        cf = open(config_file)
        config = yaml.safe_load(cf)
        cf.close()
        if config:
            for (key, value) in config.items():
                if key == 'template' and 'path_to_template' in new_config:
                    new_config.pop('path_to_template')
                new_config[key] = mdw_value(directory, value)

    if 'path_to_template' not in new_config:
        new_config['path_to_template'] = ''
    else:
        new_config['path_to_template'] += '../'

    return new_config


def get_template(config):
    tmpl = None
    if 'template' in config:
        v = config['template']
        f = os.path.join(v.origin, v.value)
        if os.path.isfile(f):
            tmpl = Template(file=f, searchList=[config])
    if not tmpl:
        tmpl = Template("$content", searchlist=[config])
    return tmpl


def get_config_and_template(directory, config):
    config = read_dir_config(directory, config)
    template = get_template(config)
    return (config, template)


def process_dir(indir, outdir, parent_config={}):

    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    (config, template) = get_config_and_template(indir, parent_config)
    for item in os.listdir(indir):
        path = os.path.join(indir, item)
        outpath = os.path.join(outdir, item)
        if os.path.isdir(path):
            process_dir(path, outpath, config)
        elif path[-3:] == '.md':
            input_file = open(path, mode="r")
            text = input_file.read()
            template.content = markdown.markdown(text)
            output_file = open(outpath[:-3] + '.html', 'w')
            output_file.write(template.respond())
        elif item == 'mdw':
            pass
        else:
            shutil.copyfile(path, outpath)


parser = argparse.ArgumentParser()
parser.add_argument('input_dir',  action=readable_dir)
parser.add_argument('output_dir', action=writeable_dir)
args = parser.parse_args()

indir = os.path.abspath(args.input_dir)
outdir = os.path.abspath(args.output_dir)

process_dir(indir, outdir)
