// Bounded, clocked D1/D2/D3 SENS evaluator, independent of old tagged Lisp.
// D2 is structure, D3:000 is EMPTY, D1:0 is PredicateBit(NO) -- distinct.
// Admitted D3 call heads: 001 QUOTE, 010 ATOM, 011 CDR, 100 CAR,
// 101 EQ (on atomic data), 111 CONS. D3:110 COND is NOT YET admitted;
// every unknown width/head, malformed D2 frame or arity fails closed.
// Boundaries: <=48 values, <=16 nesting frames, <=16 CONS cells.
module sens_d3_microcore (
    input wire clk,
    input wire rst,
    input wire word_valid,
    input wire [3:0] word_width,
    input wire [8:0] word_bits,
    input wire input_done,
    input wire input_error,
    output reg done,
    output reg valid,
    output reg error,
    output reg result_predicate,
    output reg result_bit
);
    localparam [1:0] PRED = 0, EMPTY = 1, PAIR = 2, OP = 3;
    reg [1:0] vtag [0:47];
    reg [4:0] vdata [0:47];
    reg [1:0] car_tag [0:15], cdr_tag [0:15];
    reg [4:0] car_data [0:15], cdr_data [0:15];
    reg [5:0] frame_base [0:15];
    reg frame_expect_value [0:15];
    reg [5:0] sp;
    reg [4:0] depth;
    reg [4:0] hp;
    reg root_expect_value;
    reg bad;
    reg finished;
    integer index;

    // The tasks are inlined into clocked logic by HDL synthesis.
    task push_value;
        input [1:0] tag;
        input [4:0] data;
        begin
            if (sp >= 48 || (depth == 0 && !root_expect_value)
                || (depth != 0 && !frame_expect_value[depth-1])) begin
                bad = 1;
            end else begin
                vtag[sp] = tag;
                vdata[sp] = data;
                sp = sp + 1'b1;
                if (depth == 0) root_expect_value = 0;
                else frame_expect_value[depth-1] = 0;
            end
        end
    endtask

    task close_frame;
        reg [1:0] tag;
        reg [4:0] data;
        reg [4:0] op;
        reg [5:0] first;
        reg [5:0] count;
        begin
            if (depth == 0) begin
                bad = 1;
            end else begin
                first = frame_base[depth-1];
                count = sp - first;
                if (frame_expect_value[depth-1] && count != 0) bad = 1;
                tag = EMPTY;
                data = 0;
                if (count != 0 && !bad) begin
                    if (vtag[first] != OP) bad = 1;
                    else begin
                        op = vdata[first];
                        case (op)
                            3'b001: begin // QUOTE, bounded atomic datum
                                if (count != 2 || vtag[first+1] == OP
                                    || vtag[first+1] == PAIR) bad = 1;
                                else begin
                                    tag = vtag[first+1];
                                    data = vdata[first+1];
                                end
                            end
                            3'b010: begin // ATOM
                                if (count != 2 || vtag[first+1] == OP) bad = 1;
                                else begin
                                    tag = PRED;
                                    data = (vtag[first+1] != PAIR);
                                end
                            end
                            3'b011, 3'b100: begin // CDR / CAR
                                if (count != 2 || vtag[first+1] != PAIR
                                    || vdata[first+1] >= hp) bad = 1;
                                else if (op == 3'b100) begin
                                    tag = car_tag[vdata[first+1]];
                                    data = car_data[vdata[first+1]];
                                end else begin
                                    tag = cdr_tag[vdata[first+1]];
                                    data = cdr_data[vdata[first+1]];
                                end
                            end
                            3'b101: begin // EQ, exact typed atomic equality
                                if (count != 3 || vtag[first+1] == OP
                                    || vtag[first+2] == OP
                                    || vtag[first+1] == PAIR
                                    || vtag[first+2] == PAIR) bad = 1;
                                else begin
                                    tag = PRED;
                                    data = (vtag[first+1] == vtag[first+2]
                                            && vdata[first+1] == vdata[first+2]);
                                end
                            end
                            3'b111: begin // CONS, bounded hardware pair arena
                                if (count != 3 || vtag[first+1] == OP
                                    || vtag[first+2] == OP || hp >= 16) bad = 1;
                                else begin
                                    car_tag[hp] = vtag[first+1];
                                    car_data[hp] = vdata[first+1];
                                    cdr_tag[hp] = vtag[first+2];
                                    cdr_data[hp] = vdata[first+2];
                                    tag = PAIR;
                                    data = hp[4:0];
                                    hp = hp + 1'b1;
                                end
                            end
                            default: bad = 1; // no legacy COND/truthiness
                        endcase
                    end
                end
                if (!bad) begin
                    sp = first;
                    depth = depth - 1'b1;
                    push_value(tag, data);
                end
            end
        end
    endtask

    task accept_word;
        input [3:0] width;
        input [8:0] bits;
        begin
            case (width)
                1: push_value(PRED, {4'b0, bits[0]});
                2: case (bits[1:0])
                    2'b10: begin // OPEN
                        if (depth >= 16 || (depth == 0 && !root_expect_value)
                            || (depth != 0 && !frame_expect_value[depth-1]))
                            bad = 1;
                        else begin
                            frame_base[depth] = sp;
                            frame_expect_value[depth] = 1;
                            depth = depth + 1'b1;
                        end
                    end
                    2'b00: begin // SEPARATOR
                        if (depth == 0 || frame_expect_value[depth-1]) bad = 1;
                        else frame_expect_value[depth-1] = 1;
                    end
                    2'b01: close_frame(); // CLOSE
                    default: bad = 1; // dotted pair not admitted in pilot
                endcase
                3: begin
                    if (bits[2:0] == 3'b000) push_value(EMPTY, 0);
                    else if (depth != 0 && frame_expect_value[depth-1]
                             && sp == frame_base[depth-1])
                        push_value(OP, {2'b0, bits[2:0]});
                    else bad = 1;
                end
                default: bad = 1; // D4+ requires a new explicit law
            endcase
        end
    endtask

    always @(posedge clk) begin
        if (rst) begin
            sp = 0;
            depth = 0;
            hp = 0;
            root_expect_value = 1;
            bad = 0;
            finished = 0;
            done = 0;
            valid = 0;
            error = 0;
            result_predicate = 0;
            result_bit = 0;
            for (index=0; index<16; index=index+1) begin
                frame_base[index] = 0;
                frame_expect_value[index] = 0;
                car_tag[index] = EMPTY;
                cdr_tag[index] = EMPTY;
                car_data[index] = 0;
                cdr_data[index] = 0;
            end
        end else if (!finished) begin
            if (input_error) bad = 1;
            if (word_valid && !bad) accept_word(word_width, word_bits);
            if (input_done || input_error) begin
                finished = 1;
                done = 1;
                if (bad || depth != 0 || sp != 1 || root_expect_value) begin
                    valid = 0;
                    error = 1;
                end else begin
                    valid = 1;
                    result_predicate = (vtag[0] == PRED);
                    result_bit = vdata[0][0];
                end
            end else if (bad) begin
                finished = 1;
                done = 1;
                error = 1;
                valid = 0;
            end
        end
    end
endmodule
