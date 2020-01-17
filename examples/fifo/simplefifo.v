////////////////////////////////////////////////////////////////////////////////
//
// Filename: 	simplefifo.v
//
// Project:	WBPMIC, wishbone control of a MEMs PMod MIC
//
// Purpose:	
//
// Creator:	Dan Gisselquist, Ph.D.
//		Gisselquist Technology, LLC
//
////////////////////////////////////////////////////////////////////////////////
//
// Copyright (C) 2015-2019, Gisselquist Technology, LLC
//
// This program is free software (firmware): you can redistribute it and/or
// modify it under the terms of  the GNU General Public License as published
// by the Free Software Foundation, either version 3 of the License, or (at
// your option) any later version.
//
// This program is distributed in the hope that it will be useful, but WITHOUT
// ANY WARRANTY; without even the implied warranty of MERCHANTIBILITY or
// FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
// for more details.
//
// You should have received a copy of the GNU General Public License along
// with this program.  (It's in the $(ROOT)/doc directory.  Run make with no
// target there if the PDF file isn't present.)  If not, see
// <http://www.gnu.org/licenses/> for a copy.
//
// License:	GPL, v3, as defined and found on www.gnu.org,
//		http://www.gnu.org/licenses/gpl.html
//
//
////////////////////////////////////////////////////////////////////////////////
//
//
`default_nettype	none
//
module smplfifo(i_clk, i_reset, i_wr, i_data,
		o_empty_n, i_rd, o_data, o_status, o_err);
	parameter	BW=12;	// Byte/data width
	parameter [4:0]	LGFLEN=9;	// 512 samples
	input	wire		i_clk, i_reset;
	input	wire		i_wr;
	input	wire [(BW-1):0]	i_data;
	output	wire		o_empty_n;	// True if something is in FIFO
	input	wire		i_rd;
	output	wire [(BW-1):0]	o_data;
	output	wire	[15:0]	o_status;
	output	wire		o_err;

	localparam	FLEN=(1<<LGFLEN);

	reg	[(BW-1):0]	fifo[0:(FLEN-1)];
	reg	[(LGFLEN-1):0]	r_first, r_last, r_next;

	wire	[(LGFLEN-1):0]	w_first_plus_one, w_first_plus_two,
				w_last_plus_one;
	assign	w_first_plus_two = r_first + {{(LGFLEN-2){1'b0}},2'b10};
	assign	w_first_plus_one = r_first + {{(LGFLEN-1){1'b0}},1'b1};
	assign	w_last_plus_one  = r_next; // r_last  + 1'b1;

	reg	will_overflow;
	initial	will_overflow = 1'b0;
	always @(posedge i_clk)
		if (i_reset)
			will_overflow <= 1'b0;
		else if (i_rd)
			will_overflow <= (will_overflow)&&(i_wr);
		else if (i_wr)
			will_overflow <= (will_overflow)||(w_first_plus_two == r_last);
		else if (w_first_plus_one == r_last)
			will_overflow <= 1'b1;

	// Write
	reg	r_ovfl;
	initial	r_first = 0;
	initial	r_ovfl  = 0;
	always @(posedge i_clk)
		if (i_reset)
		begin
			r_ovfl <= 1'b0;
			r_first <= { (LGFLEN){1'b0} };
		end else if (i_wr)
		begin // Cowardly refuse to overflow
			if ((i_rd)||(!will_overflow)) // (r_first+1 != r_last)
				r_first <= w_first_plus_one;
			else
				r_ovfl <= 1'b1;
		end
	always @(posedge i_clk)
		if (i_wr) // Write our new value regardless--on overflow or not
			fifo[r_first] <= i_data;

	// Reads
	//	Following a read, the next sample will be available on the
	//	next clock
	//	Clock	ReadCMD	ReadAddr	Output
	//	0	0	0		fifo[0]
	//	1	1	0		fifo[0]
	//	2	0	1		fifo[1]
	//	3	0	1		fifo[1]
	//	4	1	1		fifo[1]
	//	5	1	2		fifo[2]
	//	6	0	3		fifo[3]
	//	7	0	3		fifo[3]
	reg	will_underflow;
	initial	will_underflow = 1'b1;
	always @(posedge i_clk)
		if (i_reset)
			will_underflow <= 1'b1;
		else if (i_wr)
			will_underflow <= 1'b0;
		else if (i_rd)
			will_underflow <= (will_underflow)||(w_last_plus_one == r_first);
		else
			will_underflow <= (r_last == r_first);

	//
	// Don't report FIFO underflow errors.  These'll be caught elsewhere
	// in the system, and the logic below makes it hard to reset them.
	// We'll still report FIFO overflow, however.
	//
	// reg		r_unfl;
	// initial	r_unfl = 1'b0;
	initial	r_last = 0;
	initial	r_next = { {(LGFLEN-1){1'b0}}, 1'b1 };
	always @(posedge i_clk)
		if (i_reset)
		begin
			r_last <= 0;
			r_next <= { {(LGFLEN-1){1'b0}}, 1'b1 };
			// r_unfl <= 1'b0;
		end else if (i_rd)
		begin
			if (!will_underflow) // (r_first != r_last)
			begin
				r_last <= r_next;
				r_next <= r_last +{{(LGFLEN-2){1'b0}},2'b10};
				// Last chases first
				// Need to be prepared for a possible two
				// reads in quick succession
				// o_data <= fifo[r_last+1];
			end
			// else r_unfl <= 1'b1;
		end

	reg	[(BW-1):0]	fifo_here, fifo_next, r_data;
	always @(posedge i_clk)
		fifo_here <= fifo[r_last];
	always @(posedge i_clk)
		fifo_next <= fifo[r_next];
	always @(posedge i_clk)
		r_data <= i_data;

	reg	[1:0]	osrc;
	always @(posedge i_clk)
		if (will_underflow)
			// o_data <= i_data;
			osrc <= 2'b00;
		else if ((i_rd)&&(r_first == w_last_plus_one))
			osrc <= 2'b01;
		else if (i_rd)
			osrc <= 2'b11;
		else
			osrc <= 2'b10;
	assign o_data = (osrc[1]) ? ((osrc[0])?fifo_next:fifo_here) : r_data;

	// wire	[(LGFLEN-1):0]	current_fill;
	// assign	current_fill = (r_first-r_last);

	reg	r_empty_n;
	initial	r_empty_n = 1'b0;
	always @(posedge i_clk)
		if (i_reset)
			r_empty_n <= 1'b0;
		else casez({i_wr, i_rd, will_underflow})
			3'b00?: r_empty_n <= (r_first != r_last);
			3'b010: r_empty_n <= (r_first != w_last_plus_one);
			3'b10?: r_empty_n <= 1'b1;
			3'b110: r_empty_n <= (r_first != r_last);
			3'b111: r_empty_n <= 1'b1;
			default: begin end
		endcase

	//
	// If this is a receive FIFO, the FIFO count that matters is the number
	// of values yet to be read.  If instead this is a transmit FIFO, then 
	// the FIFO count that matters is the number of empty positions that
	// can still be filled before the FIFO is full.
	//
	// Adjust for these differences here.
	reg	[(LGFLEN-1):0]	r_fill;
	initial	r_fill = 0;
	always @(posedge i_clk)
		begin
			// Calculate the number of elements in our FIFO
			//
			// Although used for receive, this is actually the more
			// generic answer--should you wish to use the FIFO in
			// another context.
			if (i_reset)
				r_fill <= 0;
			else casez({(i_wr), (!will_overflow), (i_rd)&&(!will_underflow)})
			3'b0?1:   r_fill <= r_first - r_next;
			3'b110:   r_fill <= r_first - r_last + 1'b1;
			3'b1?1:   r_fill <= r_first - r_last;
			default: r_fill  <= r_first - r_last;
			endcase
		end

	// We don't report underflow errors.  These
	assign o_err = (r_ovfl); //  || (r_unfl);

	wire	w_half_full;
	wire	[13:0]	w_fill;
	generate
		if (LGFLEN > 14)
			assign w_fill[13:0] = r_fill[(LGFLEN-1):(LGFLEN-14)];
		else if (LGFLEN == 14)
			assign w_fill = r_fill;
		else // if (LGFLEN < 14)
		begin
			assign	w_fill[(LGFLEN-1):0] = r_fill;
			assign	w_fill[13:LGFLEN[3:0]] = 0;
		end
	endgenerate

	assign	w_half_full = r_fill[(LGFLEN-1)];

	assign	o_status = {
		// The FIFO fill--for a receive FIFO the number of elements
		// left to be read, and for a transmit FIFO the number of
		// empty elements within the FIFO that can yet be filled.
		w_fill,
		// A '1' here means a half FIFO length can be read
		w_half_full,
		// A '1' here means the FIFO can be read from (if it is a
		// receive FIFO), or be written to (if it isn't).
		r_empty_n
	};

	assign	o_empty_n = r_empty_n;

`ifdef	FORMAL

`ifdef	SMPLFIFO
`define	ASSUME	assume
`else
`define	ASSUME	assert
`endif

//
// Assumptions about our input(s)
//
//
	reg	f_past_valid, f_last_clk;

	//
	// Underflows are a very real possibility, should the user wish to read from this
	// FIFO while it is empty.  Our parent module will need to deal with this.
	//
	// always @(posedge i_clk)
	//	`ASSUME((!will_underflow)||(!i_rd)||(i_reset));
//
// Assertions about our outputs
//
//

	initial	f_past_valid = 1'b0;
	always @(posedge i_clk)
		f_past_valid <= 1'b1;

	always @(*)
	if (!f_past_valid)
		`ASSUME(i_reset);

	wire	[(LGFLEN-1):0]	f_fill, f_next;
	assign	f_fill = r_first - r_last;
	assign	f_next = r_last + 1'b1;
	always @(posedge i_clk)
	begin
		assert(f_fill == r_fill);
		if (f_fill == 0)
		begin
			assert(will_underflow);
			assert(!o_empty_n);
		end else begin
			assert(!will_underflow);
			assert(o_empty_n);
		end

		if (f_fill == {(LGFLEN){1'b1}})
			assert(will_overflow);
		else
			assert(!will_overflow);

		assert(r_next == f_next);
	end

	always @(posedge i_clk)
	if (f_past_valid)
	begin
		if ($past(i_reset))
			assert(!o_err);
		else begin
			// Underflow detection
			if (($past(i_rd))&&($past(r_fill == 0)))
			begin
				// This core doesn't report underflow errors,
				// but quietly ignores them
				//
				// assert(o_err);
				//
				// On an underflow, we need to be careful not
				// to advance the pointer.
				assert(r_last == $past(r_last));
			end
			//
			// Overflow detection
			if (($past(i_wr))&&(!$past(i_rd))
					&&($past(will_overflow)))
			begin
				// Make sure we report this result
				assert(o_err);

				// Make sure we didn't advance our write
				// pointer on overflow
				assert(r_first == $past(r_first));
			end
		end
	end

`endif
endmodule
