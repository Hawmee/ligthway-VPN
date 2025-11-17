export interface getPeerResponse{
    peer_name: string;
    config: string;
}

export interface addResponse{
    message: string;
    peer_name: string;
    ip_address: string;
    config_file: string;
    directory: string;
}

export interface responseServInfo{
    server_public_key: string,
    publickey_server_exists: boolean;
    wg0_conf_exists: boolean;
    existing_peers_count: number;
    wireguard_path: string;
}