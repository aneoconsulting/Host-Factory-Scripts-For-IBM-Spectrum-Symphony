variable user_name {}

variable tenant_name {}

variable password {}

variable auth_url {
	default = "https://auth.cloud.ovh.net/v2.0/"
}

variable region { default = "GRA5" }
variable net_public { default = "Ext-Net" }
variable net_priv { default = "vlan1" }

variable pool { default = "public" }
variable image_id { default = "__REPLACE_ME__" }

variable flavor {
	default = "win-b2-7-flex"
}

variable admin_password {
	default = "__REPLACE_ME__"
}
