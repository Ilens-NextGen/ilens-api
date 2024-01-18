#!/usr/bin/env bash
# Start the server

# host to listen on
host=${HOST:-0.0.0.0}

# port to listen on
port=${PORT:-8000}

# application to serve
asgi_app=${ASGI_APP:-"app:app"}

# maximum time to allow websocket to be connected. -1 for infinite
socket_timeout=$WEBSOCKET_TIMEOUT

# maximum time to allow a connection to be established. -1 for infinite
socket_connect_timeout=$WEBSOCKET_CONNECT_TIMEOUT

# how long to wait for worker before timing out HTTP connections
http_timeout=$HTTP_TIMEOUT

# access log file. - for stdout
access_log=${ACCESS_LOG:-"-"}

# access log format
log_fmt=$LOG_FMT

# the number of seconds an ASGI application has to
# exit after client disconnect before it is killed
application_close_timeout=$APPLICATION_CLOSE_TIMEOUT

# ASGI root path
root_path=$ROOT_PATH

# server name
server_name=$SERVER_NAME

function build_cli_args() {
    local cli_args=()

    if [[ -n "$host" ]]; then
        cli_args+=(-b "$host")
    fi

    if [[ -n "$port" ]]; then
        cli_args+=(-p "$port")
    fi

    if [[ -n "$socket_timeout" ]]; then
        cli_args+=(--websocket_timeout "$socket_timeout")
    fi

    if [[ -n "$socket_connect_timeout" ]]; then
        cli_args+=(--websocket_connect_timeout "$socket_connect_timeout")
    fi

    if [[ -n "$http_timeout" ]]; then
        cli_args+=(-t "$http_timeout")
    fi

    if [[ -n "$access_log" ]]; then
        cli_args+=(--access-log "$access_log")
    fi

    if [[ -n "$log_fmt" ]]; then
        cli_args+=(--log-fmt "'$log_fmt'")
    fi

    if [[ -n "$application_close_timeout" ]]; then
        cli_args+=(--application-close-timeout "$application_close_timeout")
    fi

    if [[ -n "$root_path" ]]; then
        cli_args+=(--root-path "$root_path")
    fi

    if [[ -n "$server_name" ]]; then
        cli_args+=(-s "$server_name")
    fi

    if [[ -n "$asgi_app" ]]; then
        cli_args+=("$asgi_app")
    fi
    echo "${cli_args[@]}"
}

cli_args="$(build_cli_args)"
echo "Starting server with args: $cli_args"
daphne $cli_args