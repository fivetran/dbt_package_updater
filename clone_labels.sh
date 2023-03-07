#!/bin/bash

cd repositories 
repo="$1"
label_name="$2"
description="$3"

cd "$repo"
gh label clone "fivetran/dbt_package_integrations" --force