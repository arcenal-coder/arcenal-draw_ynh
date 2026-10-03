#!/bin/bash

app="arcenal_draw"

install_libredwg() {
    local build_dir
    build_dir="$(mktemp -d)"
    ynh_setup_source --dest_dir="$build_dir" --source_id="libredwg"
    (
        cd "$build_dir"
        ./configure \
            --prefix="$install_dir/libredwg" \
            --disable-bindings \
            --disable-python \
            --disable-json \
            --disable-dependency-tracking \
            --disable-werror \
            CFLAGS="-O2 -w"
        make --silent -C src -j2
        make --silent -C programs -j2 dwg2dxf
        make --silent -C src install
        install -d "$install_dir/libredwg/bin"
        install -m 755 programs/.libs/dwg2dxf "$install_dir/libredwg/bin/dwg2dxf"
    )
    ynh_safe_rm "$build_dir"
    test -x "$install_dir/libredwg/bin/dwg2dxf"
}

configure_files() {
    ynh_config_add_nginx
    ynh_config_add_systemd
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
