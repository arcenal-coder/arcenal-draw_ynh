#!/bin/bash

app="arcenal_draw"

sync_public_label() {
    ynh_app_setting_set --key=label --value="Crobard"
    yunohost user permission update "$app.main" --label="Crobard"
}

configure_files() {
    ynh_config_add_nginx
    ynh_config_add_systemd
}

install_consultation_files() {
    mkdir -p "$install_dir/web/consultation/assets"
    cp "$package_root/public/index.html" "$package_root/public/viewer.js" "$package_root/public/viewer.css" "$install_dir/web/consultation/"
    cp -a "$package_root/assets/." "$install_dir/web/consultation/assets/"
}

set_runtime_permissions() {
    chown "$app:www-data" "$install_dir"
    chown -R "$app:www-data" "$install_dir/web"
    chown -R "$app:$app" "$install_dir/backend" "$data_dir"
    find "$install_dir/web" -type d -exec chmod 750 {} +
    find "$install_dir/web" -type f -exec chmod 640 {} +
    find "$install_dir/backend" -type d -exec chmod 750 {} +
    find "$install_dir/backend" -type f -exec chmod 640 {} +
    chmod 750 "$install_dir" "$data_dir" "$data_dir/uploads"
}
