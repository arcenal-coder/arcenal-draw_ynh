#!/bin/bash

app="arcenal_draw"

configure_files() {
    ynh_config_add_nginx
    ynh_config_add_systemd
}
