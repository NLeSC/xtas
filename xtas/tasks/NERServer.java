/*
 * Copyright 2014 Netherlands eScience Center.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import edu.stanford.nlp.ie.crf.CRFClassifier;
import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.ling.CoreLabel;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.InputStreamReader;
import java.lang.StringBuilder;
import java.util.List;


/*
 * Custom Stanford NER server that communicates over stdin and stdout.
 *
 * Reads lines from stdin, writes NER result (as a single line) to stdout,
 * without buffering I/O. Stops at EOF.
 */
public class NERServer {
    public static void main(String[] args) throws Exception {
        if (args.length != 1) {
            System.err.println("usage: java NERServer modelpath");
            System.exit(1);
        }

        CRFClassifier crf = CRFClassifier.getClassifier(args[0]);
        BufferedReader input = new BufferedReader(
                                     new InputStreamReader(System.in), 1);

        for (;;) {
            String ln = input.readLine();
            if (ln == null) {
                break;
            }

            List<List<CoreLabel>> out = crf.classify(ln);
            for (List<CoreLabel> sentence : out) {
                for (CoreLabel word : sentence) {
                    String label = word.get(
                                    CoreAnnotations.AnswerAnnotation.class);
                    System.out.print(word.word() + '/' + label + ' ');
                }
            }
            System.out.print('\n');
        }
    }
}
