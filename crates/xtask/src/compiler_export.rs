            .expect("ATOM compiler input");
        let request = render_request("atom", &input, "0123456789abcdef0123456789abcdef01234567");
        let artifact = render_artifact("atom", &request);
        let request_digest = sha256_hex(request.as_bytes());

        assert!(artifact.contains("(schema . compiler-compilation-artifact/1)"));
        assert!(artifact.contains(&format!("(semantic-request-sha256 . \"{request_digest}\")")));
        assert!(artifact.contains(&format!("(semantic-request . {request})")));
        assert!(artifact.contains("(artifact-status . canonical-backend-neutral)"));
        assert!(request.contains("(ідентичність . ((domain . D3) (bits . 010)))"));
        assert!(request.contains("(походження . ((repository . \"juv4uk/sens\")"));
        let legacy_a: String = ['i', 'd', 'e', 'n', 't', 'i', 't', 'y'].into_iter().collect();
        let legacy_b: String = ['p', 'r', 'o', 'v', 'e', 'n', 'a', 'n', 'c', 'e']
            .into_iter()
            .collect();
        assert!(!request.contains(&format!("({legacy_a} .")));
        assert!(!request.contains(&format!("({legacy_b} .")));
    }

    #[test]
    fn compilation_artifact_carries_no_backend_or_install_policy() {
        let input = compiler_semantic_input_from_sens(parse_identity("D4", "0010").unwrap())
            .unwrap()
            .expect("LAMBDA compiler input");
        let request = render_request("d4-0010", &input, "0123456789abcdef0123456789abcdef01234567");