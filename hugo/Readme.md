# ecmccfg HUGO documentation generator

## working on the HUGO sources locally
Github-pages (gh-pages branch) is used to host the web-site.
The static html is created by [HUGO](https://gohugo.io/) via a CI/CD pipeline (github actions).

For details take a look in the `.github/workflows` directory.

### obtaining the code
1. clone the repo `git clone <repo>`
1. change into the directory `cd <clone dir>`

***
### Prerequisites
#### HUGO
get HUGO if you don't have it already. Follow the instructions [here](https://gohugo.io/getting-started/quick-start/).

#### mdutils
```shell
pip install mdutils
```

##### build markdown documentation from doxygen sources
The markdown files are created from the doxygen information embedded in the `cmd` and `iocsh`.
The directories `'hardware', 'db', 'doc', 'examples', 'protocols', 'src'` are excluded from the parsing.
```shell
python ./hugo/doxygen2md/dox2md.py
```
This should create the `content/sources` directory in `hugo`.

***
### HUGO
1. fire up HUGO `hugo server -s ./hugo/ -D`
1. navigate in a browser to [localhost:1313](http://localhost:1313/), note the `1313` is the default port, which might differ on your system.
Observe the CLI output for details.
1. gawk at the beauty of the produced web-site :)

### editing the code
* content is found in the `content` directory
* mostly everything is done in markdown
* the HUGO theme ["learn"](http://github.com/matcornic/hugo-theme-learn) is used. Follow the instructions [here](https://learn.netlify.app/en/) for examples and an overview of it's capabilities.
* changes are reflected immediately in the browser after saving your changes.

### publish
Once you're happy with the changes, push them to the `master` branch.
This will trigger the CI/CD pipeline and the result will be visible [here](https://elnetmotion.gitpages.psi.ch/elnet-web/).


### Content structure and shared references

The manual follows this commissioning path: Quickstart, IOC startup, axis YAML
configuration, scaling and direction, homing, motor-record/autosave behavior,
and diagnostics. Section landing pages route readers to guides, examples,
reference material, and troubleshooting.

Motion configuration includes the master/slave state machine for coordinating
virtual and physical axis groups.

General configuration has three subsections:

- `general_cfg/startup/`: startup arguments and modes, validation, PV processing,
  and platform recommendations.
- `general_cfg/ethercat/`: hardware support, commissioning, timing, and FSoE.
- `general_cfg/utilities/`: script and command references, iocsh helpers, data
  buffers, lookup tables, and logger diagnostics.

The regrouped pages set an explicit `url` in front matter to preserve their
published addresses. Keep those URLs when moving or renaming sources, and use
Hugo `relref` links to the current source paths. Retain existing section anchors
when extracting material; the YAML guide's `#all-yaml-settings` heading now links
to the separate complete example.

For motor records, `motion_cfg/motor.md` explains behavior,
`motion_cfg/autosave.md` owns restore ordering and soft-limit precedence, and
`motion_cfg/best_practice/motor.md` contains example configurations and test
results. Keep example-specific values with the examples and link to the behavior
guides for general rules.

Both YAML lookup pages are generated from
`hugo/reference/axis-yaml-settings.json`. Each group has full key paths, a shared
requirement, and a detailed description. Its entries provide compact table
summaries. This retains the information from both earlier views while keeping
key requirements in one place. Requirements describe configuration guidance,
including conditional requirements; they are not a replacement for validation
by the selected YAML backend.

After editing the reference source, run from the repository root:

```shell
python3 hugo/scripts/generate_axis_reference.py
python3 hugo/scripts/generate_axis_reference.py --check
hugo --minify -s hugo
```

Edit the reference pages' introductory prose directly, but leave the marked
generated blocks to the generator. CI checks that both pages match the source.
