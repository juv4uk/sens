`timescale 1ns/1ps
module tb_sens_silicon_d3;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1;
    reg byte_valid = 0;
    reg [7:0] byte_data = 0;
    reg byte_last = 0;
    wire byte_ready, done, valid, error, result_is_predicate, result_bit;

    sens_silicon_d3 dut (
        .clk(clk), .rst(rst), .byte_valid(byte_valid),
        .byte_ready(byte_ready), .byte_data(byte_data),
        .byte_last(byte_last), .done(done), .valid(valid), .error(error),
        .result_is_predicate(result_is_predicate), .result_bit(result_bit)
    );

    // The hex is merely $readmemh's ROM image of the packed, physical T5
    // bytes. scripts/check_silicon_d3_vectors.py independently recomputes
    // it from canonical exact-width source, and checks the old empty form.
    reg [7:0] rom [0:37];
    integer cycles;
    integer k;
    integer simulation_clocks = 0;
    always @(posedge clk) begin
        if (rst) simulation_clocks <= 0;
        else simulation_clocks <= simulation_clocks + 1;
    end

    task restart;
        begin
            @(negedge clk);
            rst = 1;
            byte_valid = 0;
            byte_last = 0;
            repeat(3) @(negedge clk);
            rst = 0;
        end
    endtask

    task send_byte;
        input [7:0] payload;
        input last;
        integer guard;
        begin
            guard = 0;
            @(negedge clk);
            while (!byte_ready && guard < 200) begin
                @(negedge clk);
                guard = guard + 1;
            end
            if (!byte_ready) $fatal(1, "input receiver stuck");
            byte_data = payload;
            byte_last = last;
            byte_valid = 1;
            @(negedge clk);
            byte_valid = 0;
            byte_last = 0;
        end
    endtask

    task finish_expect;
        input integer id;
        input expected;
        input should_reject;
        integer guard;
        begin
            guard = 0;
            while (!done && guard < 500) begin
                @(negedge clk);
                guard = guard + 1;
            end
            if (!done) $fatal(1, "case %0d: no completion", id);
            if (should_reject) begin
                if (!error || valid) $fatal(1, "case %0d: unsafe program accepted", id);
                $display("SILICON_REJECT case=%0d total_sim_clocks=%0d", id, simulation_clocks);
            end else begin
                if (error || !valid || !result_is_predicate || result_bit !== expected) begin
                    $display("FAILED case=%0d done=%b valid=%b error=%b is_d1=%b bit=%b expected=%b",
                              id, done, valid, error, result_is_predicate, result_bit, expected);
                    $fatal(1, "silicon runtime mismatch");
                end
                $display("SILICON_PASS case=%0d D1=%0d total_sim_clocks=%0d", id, result_bit, simulation_clocks);
            end
        end
    endtask

    task run_case;
        input integer id;
        input integer start;
        input integer count;
        input expected;
        integer i;
        begin
            restart();
            for (i=0; i<count; i=i+1) begin
                send_byte(rom[start+i], i==count-1);
            end
            finish_expect(id, expected, 0);
        end
    endtask

    initial begin
        $readmemh("hardware/sens-silicon/tb/d3-primitives.t5.hex", rom);
        run_case(0, 0, 3, 1);    // QUOTE(1)
        run_case(1, 3, 4, 1);    // ATOM(EMPTY D3:000)
        run_case(2, 7, 7, 0);    // ATOM(CONS(1,0))
        run_case(3, 14, 10, 1);  // EQ(CAR(CONS(1,0)),1)
        run_case(4, 24, 10, 1);  // EQ(CDR(CONS(1,0)),0)
        run_case(5, 34, 4, 0);   // EQ(1,0)

        restart();
        send_byte(8'hf3, 1); // Out-of-range physical trit byte (243).
        finish_expect(6, 0, 1);
        restart();
        send_byte(8'hf2, 1); // Five padding trits; empty program blocked.
        finish_expect(7, 0, 1);
        // D1:0 is a predicate value, while D3:000 is a structural EMPTY.
        // Same numeric bits may not erase domain identity at EQ.
        restart();
        send_byte(8'h66, 0);
        send_byte(8'h89, 0);
        send_byte(8'h38, 0);
        send_byte(8'h06, 0);
        send_byte(8'ha1, 1);
        finish_expect(8, 0, 0);

        // D3:110 COND must not be silently reinterpreted as legacy truthiness.
        restart();
        send_byte(8'h67, 0);
        send_byte(8'h38, 0);
        send_byte(8'h8c, 1);
        finish_expect(9, 0, 1);
        $display("SILICON_SUITE_PASS six source cases, one D1/D3 identity case, three fail-closed cases");
        $finish;
    end
endmodule
