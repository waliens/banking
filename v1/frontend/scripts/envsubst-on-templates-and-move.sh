#!/bin/sh

set -e

ME=$(basename $0)

# cross platform realpath
# busy box realpath does not support the '--relative-to' switch
relpath () {
  local ref absolute
  ref=$(realpath $1)
  absolute=$(realpath $2)
  echo ${absolute#"$ref"}
}

auto_envsubst_and_move_all() {
  local root_directory suffix defined_envs
  root_directory=$(realpath $1)
  suffix=$2
  defined_envs=$(printf '${%s} ' $(env | cut -d= -f1))
  find "$root_directory" -follow -type f -print | while read -r found_file; do
    # relative path to root directory 
    local source_filepath source_relative_filepath target_dirpath target_filepath source_filepath_no_suffix
    source_filepath=$(realpath $found_file)
    source_relative_filepath=$(relpath $root_directory $found_file)
    target_filepath=${source_relative_filepath%%"$suffix"}
    target_dirpath=$(dirname $target_filepath)
    source_filepath_no_suffix=${source_filepath%%"$suffix"}
    if [ $(basename $source_filepath) != $(basename $target_filepath) ] && [ -f $source_filepath_no_suffix ]; then
      echo >&2 "$ME: ERROR: after env interpolation, file '$source_filepath' will have the same name as file '$source_filepath_no_suffix'"
      exit 22  # invalid argument
    fi
    # create target folder if not exists
    if [ ! -d $target_dirpath ]; then
      echo "$ME: $target_dirpath does not exists, creating hierachy..."
      mkdir -p $target_dirpath
    fi
    # check if target folder is writable
    if [ ! -w $target_dirpath ]; then
      echo >&2 "$ME: ERROR: '[$root_directory/]$source_relative_filepath' found, but its target directory '$target_dirpath' is not writable"
      exit 30  # read-only filesystem
    fi

    # file interpolation
    if [ $(basename $source_filepath) != $(basename $target_filepath) ]; then
      echo "$ME: Running envsubst on $source_filepath to $target_filepath"
      envsubst "$defined_envs" < "$source_filepath" > "$target_filepath"
    else
      echo "$ME: Copying file '$source_relative_filepath' to target '$target_filepath'"
      cp $source_filepath $target_filepath
    fi 
  done
}

CONFIG_FOLDER=${1:-"/samples"}
TEMPLATE_SUFFIX=${2:-".sample"}

if [ -d $CONFIG_FOLDER ]; then
  auto_envsubst_and_move_all $CONFIG_FOLDER $TEMPLATE_SUFFIX 
else
  echo >&2 "$ME: WARNING: configuration directory '$CONFIG_FOLDER' not found"
fi

exit 0